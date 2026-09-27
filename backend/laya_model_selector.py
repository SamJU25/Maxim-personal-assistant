"""
backend/laya_model_selector.py
==============================
Laya-Driven Intelligent Model Capability Evaluator & Router.

Evaluates user tasks (coding, deep reasoning, web browsing, vision, chat)
and matches them against capability profiles of available Local GGUF models
and connected Cloud providers (OpenAI, Claude, Gemini, DeepSeek, Groq, Perplexity).
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("maxim.laya_model_selector")


@dataclass
class ModelCapabilityProfile:
    id: str
    name: str
    provider: str  # "local", "openai", "anthropic", "google", "deepseek", "groq", "perplexity", etc.
    is_cloud: bool
    coding: float = 0.5
    deep_reasoning: float = 0.5
    web_browsing: float = 0.5
    multimodal_vision: float = 0.0
    creative_writing: float = 0.5
    speed_latency: float = 0.5  # 1.0 = ultra fast (<1s), 0.5 = moderate
    tool_use: float = 0.5
    context_window: int = 16384
    is_active_warm: bool = False
    description: str = ""
    category: str = "llm"  # "llm", "vision", "asr", "tts"


@dataclass
class TaskRequirements:
    primary_domain: str  # "coding", "deep_reasoning", "browsing", "vision", "creative", "chat", "asr", "tts"
    complexity: str  # "simple", "moderate", "frontier"
    needs_web_browsing: bool = False
    needs_multimodal_vision: bool = False
    needs_deep_reasoning: bool = False
    needs_coding: bool = False
    prefer_speed: bool = False
    confidence: float = 0.85
    reason: str = ""
    is_neural: bool = False


@dataclass
class ModelDecision:
    chosen_model: str
    provider: str
    is_cloud: bool
    task_domain: str
    complexity: str
    capability_score: float
    model_capabilities: Dict[str, float]
    reason: str
    is_neural: bool = False
    full_candidate_info: Optional[Dict[str, Any]] = None


def build_model_capability_profile(
    model_info: Dict[str, Any],
    is_active_warm: bool = False
) -> ModelCapabilityProfile:
    """
    Constructs a rich capability profile for any local GGUF or connected cloud model.
    """
    is_cloud = bool(model_info.get("is_cloud", False))
    provider = str(model_info.get("provider", "local")).lower()
    name = str(model_info.get("name", model_info.get("file_name", "")))
    name_lower = name.lower()
    m_id = str(model_info.get("id", name))
    cat = str(model_info.get("category", "llm")).lower()

    profile = ModelCapabilityProfile(
        id=m_id,
        name=name,
        provider=provider,
        is_cloud=is_cloud,
        is_active_warm=is_active_warm,
        category=cat,
        description=str(model_info.get("role_description", "")),
    )

    if is_cloud:
        # Frontier Cloud Provider Profiles
        if "anthropic" in provider or "claude" in name_lower:
            if "sonnet" in name_lower:
                profile.coding = 0.98
                profile.deep_reasoning = 0.97
                profile.web_browsing = 0.92
                profile.multimodal_vision = 0.94
                profile.tool_use = 0.98
                profile.speed_latency = 0.85
                profile.context_window = 200000
            elif "haiku" in name_lower:
                profile.coding = 0.88
                profile.deep_reasoning = 0.85
                profile.web_browsing = 0.88
                profile.multimodal_vision = 0.85
                profile.tool_use = 0.90
                profile.speed_latency = 0.98
                profile.context_window = 200000
            else:
                profile.coding = 0.95
                profile.deep_reasoning = 0.95
                profile.web_browsing = 0.90
                profile.multimodal_vision = 0.90
                profile.tool_use = 0.95
                profile.speed_latency = 0.88
                profile.context_window = 200000

        elif "openai" in provider or "chatgpt" in provider:
            if "o1" in name_lower or "o3" in name_lower:
                profile.deep_reasoning = 0.99
                profile.coding = 0.96
                profile.web_browsing = 0.70
                profile.multimodal_vision = 0.85
                profile.speed_latency = 0.60
                profile.tool_use = 0.85
                profile.context_window = 128000
            elif "4o-mini" in name_lower:
                profile.coding = 0.86
                profile.deep_reasoning = 0.84
                profile.web_browsing = 0.86
                profile.speed_latency = 0.98
                profile.tool_use = 0.92
                profile.context_window = 128000
            else:  # GPT-4o
                profile.coding = 0.94
                profile.deep_reasoning = 0.93
                profile.web_browsing = 0.90
                profile.multimodal_vision = 0.92
                profile.tool_use = 0.95
                profile.speed_latency = 0.90
                profile.context_window = 128000

        elif "google" in provider or "gemini" in name_lower:
            if "flash" in name_lower or "gemini-2" in name_lower:
                profile.speed_latency = 0.98
                profile.web_browsing = 0.96
                profile.multimodal_vision = 0.95
                profile.coding = 0.89
                profile.deep_reasoning = 0.89
                profile.tool_use = 0.94
                profile.context_window = 1048576
            else:  # Gemini Pro
                profile.deep_reasoning = 0.96
                profile.multimodal_vision = 0.96
                profile.web_browsing = 0.95
                profile.coding = 0.93
                profile.tool_use = 0.94
                profile.speed_latency = 0.88
                profile.context_window = 2097152

        elif "deepseek" in provider or "deepseek" in name_lower:
            if "r1" in name_lower or "reasoner" in name_lower:
                profile.deep_reasoning = 0.98
                profile.coding = 0.95
                profile.speed_latency = 0.70
                profile.tool_use = 0.85
                profile.context_window = 64000
            else:  # DeepSeek V3
                profile.coding = 0.93
                profile.deep_reasoning = 0.91
                profile.speed_latency = 0.90
                profile.tool_use = 0.90
                profile.context_window = 64000

        elif "perplexity" in provider:
            profile.web_browsing = 0.99
            profile.deep_reasoning = 0.86
            profile.coding = 0.80
            profile.tool_use = 0.92
            profile.speed_latency = 0.92
            profile.context_window = 128000

        elif "groq" in provider:
            profile.speed_latency = 0.99
            profile.coding = 0.86
            profile.deep_reasoning = 0.85
            profile.tool_use = 0.88
            profile.context_window = 32768

        else:
            profile.coding = 0.90
            profile.deep_reasoning = 0.90
            profile.web_browsing = 0.88
            profile.multimodal_vision = 0.80
            profile.tool_use = 0.90
            profile.speed_latency = 0.85
            profile.context_window = 128000

    else:
        # Local GGUF Models
        if cat == "vision" or "vl" in name_lower or "vision" in name_lower:
            profile.multimodal_vision = 0.95
            profile.coding = 0.75
            profile.deep_reasoning = 0.78
            profile.web_browsing = 0.80
            profile.tool_use = 0.82
            profile.speed_latency = 0.80
            profile.context_window = 16384
            profile.category = "vision"
        elif cat == "asr" or "whisper" in name_lower:
            profile.speed_latency = 0.95
            profile.category = "asr"
        elif cat == "tts" or "kokoro" in name_lower:
            profile.speed_latency = 0.95
            profile.category = "tts"
        else:
            # Local LLMs
            if "coder" in name_lower:
                profile.coding = 0.95
                profile.deep_reasoning = 0.88
                profile.web_browsing = 0.80
                profile.tool_use = 0.90
                profile.speed_latency = 0.85
                profile.context_window = 32768
            elif "9b" in name_lower or "14b" in name_lower or "32b" in name_lower:
                profile.deep_reasoning = 0.90
                profile.coding = 0.89
                profile.creative_writing = 0.90
                profile.web_browsing = 0.85
                profile.tool_use = 0.88
                profile.speed_latency = 0.75
                profile.context_window = 16384
            elif "4b" in name_lower or "3.5-4b" in name_lower or "2.5-4b" in name_lower:
                profile.coding = 0.86
                profile.deep_reasoning = 0.82
                profile.web_browsing = 0.84
                profile.tool_use = 0.88
                profile.speed_latency = 0.95
                profile.context_window = 16384
            elif "gemma" in name_lower or "2b" in name_lower or "1.5b" in name_lower:
                profile.speed_latency = 0.98
                profile.creative_writing = 0.80
                profile.coding = 0.72
                profile.deep_reasoning = 0.70
                profile.tool_use = 0.75
                profile.context_window = 8192
            else:
                profile.coding = 0.82
                profile.deep_reasoning = 0.80
                profile.web_browsing = 0.80
                profile.tool_use = 0.82
                profile.speed_latency = 0.88
                profile.context_window = 16384

            quant = str(model_info.get("quant", "")).upper()
            if "Q6" in quant or "Q8" in quant or "FP16" in quant:
                profile.coding = min(1.0, profile.coding + 0.03)
                profile.deep_reasoning = min(1.0, profile.deep_reasoning + 0.03)

    return profile


class LayaModelSelector:
    """
    Evaluates model capabilities across local GGUF models and connected cloud providers
    to select the best model for any given task.
    """

    def __init__(self, decision_engine=None):
        self._decision_engine = decision_engine

    def analyze_task(
        self,
        query: str,
        has_image: bool = False,
        has_audio: bool = False,
    ) -> TaskRequirements:
        """
        Extracts domain, complexity, and specific requirements from user input
        using Laya's non-autoregressive forward pass with resilient heuristic fallback.
        """
        if has_image:
            return TaskRequirements(
                primary_domain="vision",
                complexity="moderate",
                needs_multimodal_vision=True,
                confidence=1.0,
                reason="Explicit image attachment present",
            )
        if has_audio:
            return TaskRequirements(
                primary_domain="asr",
                complexity="moderate",
                confidence=1.0,
                reason="Explicit audio attachment present",
            )

        q_clean = (query or "").strip()
        q_lower = q_clean.lower()

        # Check browsing signals first
        is_browsing = any(k in q_lower for k in (
            "http://", "https://", "www.", ".com", ".org", "browse", "surf the web",
            "search the web", "search online", "look up online", "google this",
            "duckduckgo", "latest news", "current price", "today's news", "live documentation",
            "what happened today", "recent developments", "weather in", "stock price"
        ))

        is_coding = any(k in q_lower for k in (
            "code", "coding", "python", "typescript", "javascript", "function", "class ",
            "def ", "async def", "import ", "sql", "regex", "debug", "refactor",
            "bug", "error", "traceback", "git", "api", "endpoint", "npm", "pip"
        ))

        is_deep_reasoning = any(k in q_lower for k in (
            "architecture", "system design", "formal proof", "mathematical proof",
            "complex tradeoff", "security audit", "deep analysis", "philosophical",
            "enterprise migration", "theorem", "derive the equation"
        )) or len(q_clean.split()) > 70

        is_vision = any(k in q_lower for k in (
            "ocr", "look at this picture", "what is in this image", "inspect screenshot",
            "diagram analysis", "chart breakdown", "see image", "seeing image", "see this image",
            "generate image", "generating image", "create image", "creating image",
            "generate an image", "create an image", "generate a picture", "create a picture",
            "draw a ", "render image"
        ))

        is_creative = any(k in q_lower for k in (
            "write a poem", "story about", "creative essay", "roleplay", "write lyrics"
        ))

        is_quick = any(k in q_lower for k in (
            "hi", "hello", "hey", "who are you", "what can you do", "thanks", "ok"
        )) and len(q_clean.split()) < 10

        # Try Laya neural router if available
        if self._decision_engine and self._decision_engine.is_available:
            try:
                questions = {
                    "domain": {
                        "type": "choice",
                        "instructions": "What is the primary technical domain of this request?",
                        "criteria": {
                            "browsing": "searching the live web, current news, live facts, looking up online documentation or URLs",
                            "coding": "programming, debugging, writing functions, code review, scripts, APIs, SQL, regex",
                            "deep_reasoning": "complex planning, mathematical proof, deep multi-step architecture, formal logic",
                            "vision": "visual inspection, image analysis, diagrams, OCR, generating images, creating pictures, finding or seeing images",
                            "creative": "creative writing, storytelling, poetry, roleplay",
                            "chat": "general conversation, greetings, quick questions, simple advice"
                        }
                    },
                    "complexity": {
                        "type": "choice",
                        "instructions": "What is the complexity level of this request?",
                        "criteria": {
                            "simple": "brief, straightforward, greeting, quick answer, single-step response",
                            "moderate": "typical programming, multi-paragraph explanation, standard task",
                            "frontier": "enterprise architecture, complex formal proofs, exhaustive research across many sources"
                        }
                    }
                }
                res = self._decision_engine.predict(q_clean, questions)
                domain_ans = res.get("answers", {}).get("domain", {})
                comp_ans = res.get("answers", {}).get("complexity", {})
                
                chosen_domain = domain_ans.get("choice", "chat")
                chosen_comp = comp_ans.get("choice", "moderate")
                conf = float(domain_ans.get("answer_confidence", domain_ans.get("confidence", 0.85)))

                if is_vision:
                    chosen_domain = "vision"

                return TaskRequirements(
                    primary_domain=chosen_domain,
                    complexity=chosen_comp,
                    needs_web_browsing=(chosen_domain == "browsing" or is_browsing),
                    needs_coding=(chosen_domain == "coding"),
                    needs_deep_reasoning=(chosen_domain == "deep_reasoning" or chosen_comp == "frontier"),
                    needs_multimodal_vision=(chosen_domain == "vision"),
                    prefer_speed=(chosen_comp == "simple"),
                    confidence=conf,
                    reason=f"Laya neural classification ({chosen_domain}, {chosen_comp})",
                    is_neural=True,
                )
            except Exception as e:
                logger.debug(f"Laya neural task analysis fallback: {e}")

        # Heuristic determination
        if is_browsing:
            domain = "browsing"
        elif is_coding:
            domain = "coding"
        elif is_deep_reasoning:
            domain = "deep_reasoning"
        elif is_vision:
            domain = "vision"
        elif is_creative:
            domain = "creative"
        elif is_quick:
            domain = "chat"
        else:
            domain = "chat"

        complexity = "frontier" if is_deep_reasoning else ("simple" if is_quick else "moderate")

        return TaskRequirements(
            primary_domain=domain,
            complexity=complexity,
            needs_web_browsing=is_browsing,
            needs_coding=is_coding,
            needs_deep_reasoning=is_deep_reasoning,
            needs_multimodal_vision=is_vision,
            prefer_speed=is_quick,
            confidence=0.85,
            reason=f"Pattern-matched task requirements ({domain}, {complexity})",
            is_neural=False,
        )

    def select_best_model(
        self,
        query: str,
        task_type: str = "auto",
        has_image: bool = False,
        has_audio: bool = False,
        candidates: Optional[List[Dict[str, Any]]] = None,
        cloud_providers: Optional[List[Dict[str, Any]]] = None,
        running_model_path: Optional[str] = None,
    ) -> ModelDecision:
        """
        Scores all candidate local models and connected cloud providers against
        task demands using Laya intelligence.
        """
        task_reqs = self.analyze_task(query, has_image=has_image, has_audio=has_audio)

        # Build candidate profiles
        profiles: List[Tuple[ModelCapabilityProfile, Dict[str, Any]]] = []

        all_candidates = list(candidates or [])
        for cand in all_candidates:
            is_warm = False
            if running_model_path and cand.get("path"):
                is_warm = (
                    cand.get("path") == running_model_path
                    or cand.get("id") == running_model_path
                    or cand.get("file_name") == running_model_path
                )
            prof = build_model_capability_profile(cand, is_active_warm=is_warm)
            profiles.append((prof, cand))

        # Add connected cloud providers
        for cp in (cloud_providers or []):
            cloud_cand = {
                "id": f"cloud:{cp['provider']}:{cp['model_name']}",
                "repo_id": cp["provider"],
                "name": f"{cp.get('name', cp['provider'].title())} ({cp['model_name']})",
                "file_name": cp["model_name"],
                "path": f"cloud:{cp['provider']}",
                "is_cloud": True,
                "provider": cp["provider"],
                "category": "llm",
                "role_description": f"Frontier cloud intelligence via {cp.get('name', cp['provider'].title())}",
            }
            prof = build_model_capability_profile(cloud_cand, is_active_warm=False)
            profiles.append((prof, cloud_cand))

        if not profiles:
            return ModelDecision(
                chosen_model="default",
                provider="local",
                is_cloud=False,
                task_domain=task_reqs.primary_domain,
                complexity=task_reqs.complexity,
                capability_score=0.5,
                model_capabilities={},
                reason="No candidate models found; using default fallback.",
            )

        q_lower = (query or "").lower()
        explicit_cloud_requested = any(k in q_lower for k in (
            "cloud", "frontier", "claude", "gpt-4", "gpt4", "gemini", "deepseek", "sonnet", "o1", "o3", "r1"
        ))
        explicit_local_requested = any(k in q_lower for k in ("local", "offline", "private", "on-device"))

        best_score = -1.0
        best_match: Optional[Tuple[ModelCapabilityProfile, Dict[str, Any]]] = None

        has_llm_candidate = any(p[0].category == "llm" for p in profiles)
        for prof, cand in profiles:
            # Filter non-matching auxiliary categories
            if task_reqs.primary_domain in ("coding", "deep_reasoning", "browsing", "chat", "creative"):
                if prof.category == "vision" and has_llm_candidate:
                    continue
            if task_reqs.primary_domain == "vision" and prof.category not in ("vision", "llm"):
                continue
            if task_reqs.primary_domain == "asr" and prof.category != "asr":
                continue
            if task_reqs.primary_domain == "tts" and prof.category != "tts":
                continue

            score = 0.0

            # 1. Base Domain Capability Fit
            if task_reqs.primary_domain == "coding":
                score = (
                    0.50 * prof.coding
                    + 0.25 * prof.deep_reasoning
                    + 0.15 * prof.tool_use
                    + 0.10 * prof.speed_latency
                )
            elif task_reqs.primary_domain == "browsing":
                score = (
                    0.45 * prof.web_browsing
                    + 0.30 * prof.tool_use
                    + 0.15 * prof.deep_reasoning
                    + 0.10 * prof.speed_latency
                )
            elif task_reqs.primary_domain == "deep_reasoning":
                score = (
                    0.55 * prof.deep_reasoning
                    + 0.25 * prof.coding
                    + 0.10 * prof.tool_use
                    + 0.10 * (1.0 if prof.context_window >= 32768 else 0.7)
                )
            elif task_reqs.primary_domain == "vision":
                score = (
                    0.65 * prof.multimodal_vision
                    + 0.20 * prof.deep_reasoning
                    + 0.15 * prof.speed_latency
                )
            elif task_reqs.primary_domain == "creative":
                score = (
                    0.50 * prof.creative_writing
                    + 0.30 * prof.deep_reasoning
                    + 0.20 * prof.speed_latency
                )
            else:  # chat
                score = (
                    0.55 * prof.speed_latency
                    + 0.30 * prof.deep_reasoning
                    + 0.15 * prof.creative_writing
                )

            # 2. Complexity Adjustments
            if task_reqs.complexity == "frontier":
                if prof.deep_reasoning >= 0.94:
                    score += 0.20
            elif task_reqs.complexity == "simple":
                if prof.speed_latency >= 0.90:
                    score += 0.20

            # 3. Warm Local Affinity
            if prof.is_active_warm and not prof.is_cloud:
                score += 0.25

            # 4. Explicit User Intent Overrides
            if explicit_cloud_requested and prof.is_cloud:
                score += 0.80
            if explicit_local_requested and not prof.is_cloud:
                score += 0.80

            # 5. Local Privacy & Zero-Latency Bias for Normal Tasks
            # If not frontier and not explicitly cloud, grant a modest +0.10 to local models
            if not prof.is_cloud and not explicit_cloud_requested and task_reqs.complexity != "frontier":
                score += 0.10

            if score > best_score:
                best_score = score
                best_match = (prof, cand)

        if not best_match:
            best_match = profiles[0]
            best_score = 0.5

        chosen_prof, chosen_cand = best_match

        capabilities_dict = {
            "coding": chosen_prof.coding,
            "deep_reasoning": chosen_prof.deep_reasoning,
            "web_browsing": chosen_prof.web_browsing,
            "multimodal_vision": chosen_prof.multimodal_vision,
            "speed_latency": chosen_prof.speed_latency,
            "tool_use": chosen_prof.tool_use,
            "context_window": float(chosen_prof.context_window),
        }

        tier_str = "Cloud Online" if chosen_prof.is_cloud else ("Local Warm GPU" if chosen_prof.is_active_warm else "Local Disk")
        reason_str = (
            f"Laya System 1: Selected '{chosen_prof.name}' ({tier_str}, "
            f"domain: {task_reqs.primary_domain}, complexity: {task_reqs.complexity}, "
            f"fit score: {best_score:.2f})"
        )

        return ModelDecision(
            chosen_model=chosen_cand.get("file_name", chosen_prof.name),
            provider=chosen_prof.provider,
            is_cloud=chosen_prof.is_cloud,
            task_domain=task_reqs.primary_domain,
            complexity=task_reqs.complexity,
            capability_score=round(best_score, 3),
            model_capabilities=capabilities_dict,
            reason=reason_str,
            is_neural=task_reqs.is_neural,
            full_candidate_info=chosen_cand,
        )


# Global singleton selector
laya_model_selector = LayaModelSelector()
