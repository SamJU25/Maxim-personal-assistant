"""
Unit and integration tests for Magnitude Hardware Profiler & Model Recommender.
"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from magnitude_engine import MagnitudeEngine

@pytest.fixture
def temp_magnitude():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_magnitude.db"
    engine = MagnitudeEngine(db_path=db_path)
    yield engine, tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_profile_hardware(temp_magnitude):
    engine, _ = temp_magnitude
    prof = engine.profile_hardware()
    assert "profile_id" in prof
    assert prof["cpu_cores"] >= 1
    assert prof["ram_total_gb"] > 0
    assert len(prof["recommendations"]) >= 5
    
    # Check that presets are evaluated
    recs = prof["recommendations"]
    model_names = [r["model"] for r in recs]
    assert any("Llama 3.2 3B" in m for m in model_names)
    assert any("Qwen 2.5 Coder 14B" in m for m in model_names)
    assert all("tier" in r and "target_task" in r for r in recs)

def test_calculate_recommendations_logic(temp_magnitude):
    engine, _ = temp_magnitude
    # Simulated high-end GPU with 24GB VRAM and 64GB RAM
    recs = engine._calculate_recommendations(ram_total=64.0, ram_avail=48.0, gpu_vram=24.0)
    # 3B, 8B, 14B, and 32B should fit in GPU VRAM
    fit_gpu = [r for r in recs if r["tier"] == "optimal_gpu_full_speed"]
    assert len(fit_gpu) >= 4

    # Simulated lower-end system with 8GB RAM, 0 VRAM
    recs_low = engine._calculate_recommendations(ram_total=8.0, ram_avail=6.0, gpu_vram=0.0)
    # 70B should exceed hardware capacity
    exceed = [r for r in recs_low if r["tier"] == "exceeds_hardware_capacity"]
    assert any("70B" in r["model"] for r in exceed)

def test_benchmark_throughput(temp_magnitude):
    engine, _ = temp_magnitude
    bench = engine.benchmark_throughput(test_tokens=50)
    assert bench["status"] == "benchmark_completed"
    assert bench["tokens_benchmarked"] == 50
    assert bench["estimated_tok_per_sec"] > 0

def test_get_latest_profile(temp_magnitude):
    engine, _ = temp_magnitude
    prof1 = engine.profile_hardware()
    latest = engine.get_latest_profile()
    assert latest is not None
    assert latest["cpu_cores"] == prof1["cpu_cores"]

def test_engine_tool_dispatch():
    from engine import agent_engine

    # Test magnitude_profile_hardware
    res_raw = agent_engine.execute_tool(
        name="magnitude_profile_hardware",
        args={},
        session_id="test_session"
    )
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert "profile" in res

    # Test magnitude_benchmark_throughput
    res_raw2 = agent_engine.execute_tool(
        name="magnitude_benchmark_throughput",
        args={"test_tokens": 20},
        session_id="test_session"
    )
    res2 = json.loads(res_raw2)
    assert res2["status"] == "benchmark_completed"

    # Test magnitude_get_profile
    res_raw3 = agent_engine.execute_tool(
        name="magnitude_get_profile",
        args={},
        session_id="test_session"
    )
    res3 = json.loads(res_raw3)
    assert res3["status"] == "success"
