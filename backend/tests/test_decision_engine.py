"""
backend/tests/test_decision_engine.py
=====================================
Unit tests for the Laya System 1 Decision Engine.
Verifies pre-LLM intent routing, post-LLM response verification,
and tool execution safety evaluation.
"""

import pytest
from decision_engine import (
    DecisionEngine,
    IntentDecision,
    ResponseVerification,
    ToolSafetyDecision,
    decision_engine,
)


def test_language_detection():
    # English Latin script
    res_en = decision_engine.detect_language("Hello, how are you doing today?")
    assert res_en["model"] == "english"

    # Multilingual script (e.g. Bangla)
    res_bn = decision_engine.detect_language("কেমন আছেন? আপনি কি বাংলা বুঝতে পারেন?")
    assert res_bn["model"] == "multilingual"


def test_intent_classification_explicit_attachments():
    # Explicit image
    img_decision = decision_engine.classify_intent("Look at this", has_image=True)
    assert img_decision.modality == "vision"
    assert img_decision.target_category == "vision"

    # Explicit audio
    audio_decision = decision_engine.classify_intent("Transcribe this", has_audio=True)
    assert audio_decision.modality == "asr"
    assert audio_decision.target_category == "asr"


def test_intent_classification_neural_or_heuristic():
    # Coding prompt
    code_decision = decision_engine.classify_intent(
        "Please debug this Python error: TypeError: cannot unpack non-iterable NoneType object"
    )
    assert code_decision.modality == "coding"
    assert code_decision.target_category == "llm"

    # General chat prompt
    chat_decision = decision_engine.classify_intent(
        "Tell me an interesting story about space exploration"
    )
    assert chat_decision.modality in ("chat", "coding")
    assert chat_decision.target_category == "llm"


def test_post_llm_response_verification():
    user_query = "Hey, how many languages can you speak?"
    good_reply = "I can communicate in English, Bangla, and several other languages fluently."
    bad_reply = "The human tailbone, also known as the coccyx, is a triangular bone located at the base of the spine."

    good_verif = decision_engine.verify_response(user_query, good_reply)
    bad_verif = decision_engine.verify_response(user_query, bad_reply)

    assert good_verif.addresses_query is True
    assert good_verif.drift_detected is False

    # The off-topic reply should score drastically lower or be flagged as drift
    assert bad_verif.addresses_prob < good_verif.addresses_prob
    assert bad_verif.drift_detected is True or bad_verif.addresses_prob < 0.05


def test_tool_safety_evaluation():
    # Safe read-only tool
    safe_res = decision_engine.evaluate_tool_safety("read_file", {"path": "README.md"})
    assert safe_res.is_allowed is True
    assert safe_res.risk_level == "safe"

    # Destructive shell command pattern
    danger_res = decision_engine.evaluate_tool_safety(
        "run_command", {"command": "rm -rf / --no-preserve-root"}
    )
    assert danger_res.is_allowed is False
    assert danger_res.risk_level == "dangerous"


def test_fallback_when_uninitialized():
    engine = DecisionEngine(preload=False)
    # Manually simulate uninitialized or unavailable router
    engine._init_attempted = True
    engine._router = None
    engine._available = False

    fallback_intent = engine.classify_intent("def quicksort(arr):")
    assert fallback_intent.modality == "coding"
    assert fallback_intent.is_neural is False

    fallback_safety = engine.evaluate_tool_safety("run_command", {"command": "echo test"})
    assert fallback_safety.is_allowed is True
    assert fallback_safety.risk_level == "caution"


def test_decision_rest_endpoints():
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)

    # 1. Route endpoint
    res_route = client.post("/api/decision/route", json={
        "query": "Can you inspect this photo chart?",
        "has_image": True
    })
    assert res_route.status_code == 200
    data_route = res_route.json()
    assert data_route["status"] == "success"
    assert data_route["target_category"] == "vision"

    # 2. Verify endpoint
    res_verif = client.post("/api/decision/verify", json={
        "user_query": "What time is it in Tokyo?",
        "assistant_reply": "It is currently 5:30 AM in Tokyo, Japan."
    })
    assert res_verif.status_code == 200
    data_verif = res_verif.json()
    assert data_verif["status"] == "success"
    assert data_verif["addresses_query"] is True
    assert data_verif["drift_detected"] is False

    # 3. Safety endpoint
    res_safe = client.post("/api/decision/safety", json={
        "tool_name": "run_command",
        "arguments": {"command": "format c:"}
    })
    assert res_safe.status_code == 200
    data_safe = res_safe.json()
    assert data_safe["status"] == "success"
    assert data_safe["is_allowed"] is False
    assert data_safe["risk_level"] == "dangerous"


def test_laya_model_capability_selection():
    """Verifies that Laya evaluates task demands and matches them against model capability profiles."""
    local_candidates = [
        {
            "id": "Qwen3.5-4B-Q6_K.gguf",
            "file_name": "Qwen3.5-4B-Q6_K.gguf",
            "name": "Qwen3.5-4B",
            "category": "llm",
            "quant": "Q6_K",
            "is_cloud": False,
            "path": "F:\\MAXIM V2\\models\\llm\\Qwen3.5-4B-Q6_K.gguf",
        },
        {
            "id": "Qwen2-VL-7B-Instruct.gguf",
            "file_name": "Qwen2-VL-7B-Instruct.gguf",
            "name": "Qwen2-VL-7B",
            "category": "vision",
            "quant": "Q4_K_M",
            "is_cloud": False,
            "path": "F:\\MAXIM V2\\models\\vision\\Qwen2-VL-7B-Instruct.gguf",
        },
    ]
    cloud_candidates = [
        {
            "provider": "anthropic",
            "name": "Anthropic Claude",
            "model_name": "claude-3-5-sonnet-20241022",
            "is_cloud": True,
        },
        {
            "provider": "perplexity",
            "name": "Perplexity",
            "model_name": "sonar-pro",
            "is_cloud": True,
        }
    ]

    # 1. Vision query -> selects vision model
    dec_vision = decision_engine.select_suitable_model(
        query="Inspect this diagram and tell me what the architecture represents",
        candidates=local_candidates,
        cloud_providers=cloud_candidates,
        has_image=True,
    )
    assert dec_vision.task_domain == "vision"
    assert "VL" in dec_vision.chosen_model

    # 2. Frontier enterprise reasoning query -> chooses frontier Claude
    dec_frontier = decision_engine.select_suitable_model(
        query="Design a comprehensive enterprise architecture and formal cryptographic proof for cross-chain zero-knowledge bridges",
        candidates=local_candidates,
        cloud_providers=cloud_candidates,
    )
    assert dec_frontier.is_cloud is True
    assert dec_frontier.provider == "anthropic"

    # 3. Standard local coding task with warm local model -> selects local warm Qwen
    dec_local = decision_engine.select_suitable_model(
        query="def calculate_fibonacci(n: int) -> int:",
        candidates=local_candidates,
        cloud_providers=cloud_candidates,
        running_model_path="F:\\MAXIM V2\\models\\llm\\Qwen3.5-4B-Q6_K.gguf",
    )
    assert dec_local.is_cloud is False
    assert "4B" in dec_local.chosen_model


def test_laya_browsing_need_detection():
    """Verifies that Laya detects when live web research is required."""
    # Queries needing live web search
    res_news = decision_engine.evaluate_browsing_need("What is the latest news today regarding quantum computing?")
    assert res_news.needs_browsing is True

    res_url = decision_engine.evaluate_browsing_need("Please read https://github.com/anthropics/anthropic-sdk-python")
    assert res_url.needs_browsing is True

    # Queries not needing web search
    res_code = decision_engine.evaluate_browsing_need("Write a python function to reverse a list")
    assert res_code.needs_browsing is False


def test_laya_browsing_action_and_verification():
    """Verifies Laya element selection and page content verification."""
    elements = [
        {"index": 1, "element_type": "link", "text": "Home", "href": "https://docs.example.com/"},
        {"index": 2, "element_type": "input_text", "name": "search", "placeholder": "Search documentation..."},
        {"index": 3, "element_type": "link", "text": "API Reference & SDK", "href": "https://docs.example.com/api"},
    ]

    # Searching for API docs -> selects search input or API Reference
    action_dec = decision_engine.select_browsing_action(
        objective="Find API Reference documentation",
        current_url="https://docs.example.com/",
        elements=elements,
    )
    assert action_dec.element_index in (2, 3)

    # Content verification
    sample_content = (
        "MaxIM 2.0 API Reference. MaxIM provides high-speed System 1 decisions via Laya "
        "and autonomous DOM parsing for browser automation. Endpoints include /api/chat and /api/decision."
    )
    verif_good = decision_engine.verify_browsing_content(
        objective="What endpoints does MaxIM provide?",
        content=sample_content,
    )
    assert verif_good.answers_objective is True
    assert len(verif_good.key_findings) > 0


def test_laya_decision_rest_endpoints_extended():
    """Verifies the new REST endpoints for model selection and browsing."""
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)

    # 1. Select-model endpoint
    res_model = client.post("/api/decision/select-model", json={
        "query": "Write a fast python quicksort algorithm",
        "task_type": "auto"
    })
    assert res_model.status_code == 200
    data_m = res_model.json()
    assert data_m["status"] == "success"
    assert "chosen_model" in data_m
    assert "capabilities" in data_m

    # 2. Browsing decision endpoint (need check)
    res_browse_need = client.post("/api/decision/browsing", json={
        "query": "What is the latest release of TypeScript 5.8?",
        "action": "evaluate_need"
    })
    assert res_browse_need.status_code == 200
    data_bn = res_browse_need.json()
    assert data_bn["status"] == "success"
    assert data_bn["needs_browsing"] is True


