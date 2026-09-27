"""
Unit tests for Hermes Connection Providers Roster and Sub-Cent Usage Pricing Engine.
Verifies:
1. Roster of connection providers (OpenRouter, Nous Portal, Anthropic, Groq, Mistral, xAI, Together, Fireworks, Cerebras, Perplexity, Cohere, SambaNova, Azure, etc.).
2. Provider alias resolution (chatgpt, claude, grok, gemini, nous-portal, etc.).
3. Provider custom headers (OpenRouter HTTP-Referer and X-Title).
4. Sub-cent cost formatting rules (0.00 -> $0.00, < 0.01 -> ~$0.0046, underflow -> ~$<0.0001, >= 0.01 -> ~$1.23).
5. High-efficiency model cost calculations (Groq, DeepSeek, Gemini Flash Lite, Nous 405B).
6. SQLite Cost Ledger record sub-cent tracking and daily spend summary labels.
7. FastAPI `/api/hardware/pricing` and `/api/providers` endpoints.
"""
from decimal import Decimal
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from router import model_router, ProviderType, ProviderConfig
from hardware_governor import (
    HardwareGovernorEngine,
    format_cost_label,
    _SUBCENT_THRESHOLD,
    PROVIDER_PRICING,
)
from server import app

client = TestClient(app)

def test_hermes_providers_roster():
    """Verify all Hermes connection providers exist with valid configurations."""
    expected_providers = [
        ProviderType.OLLAMA,
        ProviderType.OPENAI,
        ProviderType.GOOGLE,
        ProviderType.DEEPSEEK,
        ProviderType.OPENROUTER,
        ProviderType.NOUS,
        ProviderType.ANTHROPIC,
        ProviderType.GROQ,
        ProviderType.MISTRAL,
        ProviderType.XAI,
        ProviderType.TOGETHER,
        ProviderType.FIREWORKS,
        ProviderType.CEREBRAS,
        ProviderType.PERPLEXITY,
        ProviderType.COHERE,
        ProviderType.SAMBANOVA,
        ProviderType.AZURE,
        ProviderType.OMNIROUTE,
        ProviderType.CUSTOM,
    ]
    for p in expected_providers:
        cfg = model_router.get_provider_config(p)
        assert isinstance(cfg, ProviderConfig)
        assert cfg.name == p.value
        assert len(cfg.base_url) > 0
        assert len(cfg.default_model) > 0

def test_provider_alias_resolution():
    """Verify alias names resolve to their canonical providers."""
    aliases = {
        "chatgpt": "openai",
        "gemini": "google",
        "claude": "anthropic",
        "grok": "xai",
        "nous-portal": "nous",
        "together-ai": "together",
        "fireworks-ai": "fireworks",
        "cerebras-ai": "cerebras",
        "azure-openai": "azure",
        "azure-foundry": "azure",
    }
    for alias, canonical in aliases.items():
        cfg = model_router.get_provider_config(alias)
        assert cfg.name == canonical

def test_openrouter_custom_headers():
    """Verify OpenRouter receives required referral and attribution headers."""
    cfg = model_router.get_provider_config(ProviderType.OPENROUTER)
    assert cfg.headers.get("HTTP-Referer") == "https://maxim.local"
    assert cfg.headers.get("X-Title") == "MaxIM Agent"

def test_subcent_formatting_rules():
    """Verify Hermes-style sub-cent formatting logic prevents displaying micro-costs as $0.00."""
    # Zero stays clean
    assert format_cost_label(0.0) == "$0.00"
    assert format_cost_label(0) == "$0.00"
    assert format_cost_label(Decimal("0")) == "$0.00"

    # Sub-cent values (< $0.01) render to 4 decimal places
    assert format_cost_label(0.0046) == "~$0.0046"
    assert format_cost_label(0.0099) == "~$0.0099"
    assert format_cost_label(0.0001) == "~$0.0001"

    # Underflow boundary (amounts below 0.00005 that would otherwise round to 0.0000)
    assert format_cost_label(0.00003) == "~$<0.0001"
    assert format_cost_label(0.00001) == "~$<0.0001"

    # Standard values (>= $0.01) render to 2 decimal places
    assert format_cost_label(0.01) == "~$0.01"
    assert format_cost_label(1.234) == "~$1.23"
    assert format_cost_label(25.50) == "~$25.50"

def test_subcent_cost_calculation():
    """Verify micro-cost calculations across budget-friendly models."""
    # 1. Groq llama-3.1-8b ($0.05 / $0.08 per 1M)
    cost_groq, _ = HardwareGovernorEngine.calculate_cost("groq", "llama-3.1-8b", 1000, 500)
    # in: 1000/1M * 0.05 = 0.00005, out: 500/1M * 0.08 = 0.00004 -> total = 0.00009
    assert round(cost_groq, 6) == 0.00009
    assert format_cost_label(cost_groq) == "~$0.0001"

    # 2. DeepSeek Chat ($0.14 / $0.28 per 1M)
    cost_ds, _ = HardwareGovernorEngine.calculate_cost("deepseek", "deepseek-chat", 5000, 1000)
    # in: 5000/1M * 0.14 = 0.0007, out: 1000/1M * 0.28 = 0.00028 -> total = 0.00098
    assert round(cost_ds, 6) == 0.00098
    assert format_cost_label(cost_ds) == "~$0.0010"

    # 3. Nous Hermes 3 405B ($2.00 / $5.00 per 1M)
    cost_nous, _ = HardwareGovernorEngine.calculate_cost("nous", "hermes-3-llama-3.1-405b", 10000, 2000)
    # in: 10000/1M * 2.0 = 0.02, out: 2000/1M * 5.0 = 0.01 -> total = 0.03
    assert round(cost_nous, 4) == 0.03
    assert format_cost_label(cost_nous) == "~$0.03"

    # 4. Anthropic Claude 3.5 Sonnet ($3.00 / $15.00 per 1M) via alias 'claude'
    cost_claude, _ = HardwareGovernorEngine.calculate_cost("claude", "claude-3-5-sonnet", 1000, 1000)
    # in: 0.003, out: 0.015 -> total = 0.018
    assert round(cost_claude, 4) == 0.018
    assert format_cost_label(cost_claude) == "~$0.02"

def test_cost_ledger_subcent_record(tmp_path: Path):
    """Verify cost ledger records and spend summaries capture sub-cent labels."""
    engine = HardwareGovernorEngine(db_path=tmp_path / "ledger_test.db")
    rec = engine.record_usage(
        provider="groq",
        model="llama-3.1-8b",
        input_tokens=1000,
        output_tokens=500,
        session_id="subcent_session",
    )
    assert rec.provider == "groq"
    assert rec.estimated_cost_usd > 0
    assert rec.cost_label == "~$0.0001"

    summary = engine.get_spend_summary_today()
    assert summary["total_turns"] == 1
    assert "spend_today_label" in summary
    assert summary["spend_today_label"] == "~$0.0001"
    assert summary["by_provider"][0]["cost_label"] == "~$0.0001"

def test_pricing_catalog():
    """Verify HardwareGovernorEngine.get_pricing_catalog() contains full provider registry."""
    catalog = HardwareGovernorEngine.get_pricing_catalog()
    assert catalog["subcent_threshold_usd"] == 0.01
    assert catalog["subcent_precision_decimals"] == 4
    providers = catalog["providers"]
    assert "openrouter" in providers
    assert "nous" in providers
    assert "anthropic" in providers
    assert "groq" in providers
    assert "xai" in providers
    assert "together" in providers
    assert "fireworks" in providers
    assert "cerebras" in providers
    assert "perplexity" in providers
    assert "cohere" in providers
    assert "sambanova" in providers
    assert "azure" in providers

def test_fastapi_providers_and_pricing_endpoints():
    """Verify /api/providers and /api/hardware/pricing endpoints serve expanded metadata."""
    # 1. /api/providers
    res_prov = client.get("/api/providers")
    assert res_prov.status_code == 200
    data_prov = res_prov.json()
    prov_map = data_prov["providers"]
    for expected in ["openrouter", "nous", "anthropic", "groq", "xai", "together", "fireworks", "cerebras"]:
        assert expected in prov_map

    # 2. /api/hardware/pricing
    res_price = client.get("/api/hardware/pricing")
    assert res_price.status_code == 200
    data_price = res_price.json()
    assert data_price["subcent_threshold_usd"] == 0.01
    assert "providers" in data_price
    assert "groq" in data_price["providers"]
    assert "llama-3.1-8b" in data_price["providers"]["groq"]
