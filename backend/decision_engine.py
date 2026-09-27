"""
backend/decision_engine.py
==========================
High-speed System 1 Decision Engine powered by Laya (ModernBERT / mmBERT).
Executes non-autoregressive typed decisions (choice, score, noul) in single
forward passes (30-35ms GPU, ~250ms CPU) for:
1. Pre-LLM Task & Language Routing
2. Post-LLM Topic Drift & Hallucination Verification
3. Tool Execution Safety Scoring
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class IntentDecision:
    modality: str  # "chat", "coding", "vision", "system_cmd"
    target_category: str  # "llm", "vision", "asr", "tts"
    language: str  # "english", "multilingual"
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)
    is_neural: bool = False
    reason: str = ""


@dataclass
class ResponseVerification:
    is_valid: bool
    addresses_query: bool
    confidence: float
    drift_detected: bool
    addresses_prob: float = 0.0
    reason: str = ""
    is_neural: bool = False


@dataclass
class ToolSafetyDecision:
    is_allowed: bool
    risk_level: str  # "safe", "caution", "dangerous"
    confidence: float
    reason: str = ""
    is_neural: bool = False


class DecisionEngine:
    """
    MaxIM System 1 Decision Engine.
    Wraps Laya Router with defensive fallbacks and instant heuristic support.
    """

    def __init__(self, preload: bool = False, device: str = "cpu"):
        self.device = device
        self._router = None
        self._init_attempted = False
        self._available = False

        if preload:
            self._ensure_router()

    def _ensure_router(self):
        """Lazily initialize the Laya Router."""
        if self._init_attempted:
            return self._router

        self._init_attempted = True
        try:
            from laya import Router
            self._router = Router(device=self.device)
            self._available = True
            logger.info("Laya Decision Engine initialized successfully on %s", self.device)
        except Exception as e:
            logger.warning("Could not initialize Laya Router, running with heuristic fallback: %s", e)
            self._router = None
            self._available = False

        return self._router

    @property
    def is_available(self) -> bool:
        router = self._ensure_router()
        return router is not None and self._available

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Sub-millisecond language and script detection using Laya's pure Python router.
        """
        router = self._ensure_router()
        if router is not None:
            try:
                res = router.route(text)
                return {
                    "model": res.model,  # "english" or "multilingual"
                    "reason": getattr(res, "reason", "Detected via Laya script router"),
                    "is_neural": False
                }
            except Exception as e:
                logger.debug("Laya language detection fallback: %s", e)

        # Heuristic fallback: check for non-Latin unicode characters
        has_non_latin = any(ord(c) > 0x024F for c in text if c.isalpha())
        return {
            "model": "multilingual" if has_non_latin else "english",
            "reason": "Unicode heuristic check",
            "is_neural": False
        }

    def classify_intent(
        self,
        query: str,
        has_image: bool = False,
        has_audio: bool = False
    ) -> IntentDecision:
        """
        Pre-LLM routing: Classifies user prompt into target capability in a single pass.
        """
        if has_image:
            return IntentDecision(
                modality="vision",
                target_category="vision",
                language="english",
                confidence=1.0,
                is_neural=False,
                reason="Explicit image payload attached"
            )
        if has_audio:
            return IntentDecision(
                modality="asr",
                target_category="asr",
                language="english",
                confidence=1.0,
                is_neural=False,
                reason="Explicit audio payload attached"
            )

        q_clean = (query or "").strip()
        if not q_clean:
            return IntentDecision(
                modality="chat",
                target_category="llm",
                language="english",
                confidence=1.0,
                is_neural=False,
                reason="Empty input"
            )

        lang_info = self.detect_language(q_clean)
        lang_model = lang_info.get("model", "english")

        q_lower = q_clean.lower()

        # High-signal quick heuristic filter
        is_generation = any(k in q_lower for k in (
            "generate image", "generating image", "create image", "creating image",
            "draw a", "draw ", "render image", "generate a picture", "create a picture",
            "make a picture", "make an image", "picture of a", "photo of a", "illustration of"
        ))
        if not is_generation and any(k in q_lower for k in (
            "ocr", "visual inspection", "look at this", "look at the image",
            "what does the picture look like", "what is in this photo", "what do you see",
            "describe the image", "see image", "seeing image", "screenshot analysis", "inspect image"
        )):
            return IntentDecision(
                modality="vision",
                target_category="vision",
                language=lang_model,
                confidence=0.95,
                is_neural=False,
                reason="High-signal visual perception keyword match"
            )

        if any(k in q_lower for k in ("speech to text", "voice to text", "transcribe", "listen to audio", "audio to text", "transcription")):
            return IntentDecision(
                modality="asr",
                target_category="asr",
                language=lang_model,
                confidence=0.95,
                is_neural=False,
                reason="High-signal speech recognition keyword match"
            )

        if any(k in q_lower for k in ("text to voice", "text to speech", "speak this", "read aloud", "say aloud", "voice output", "tts", "synthesize voice")):
            return IntentDecision(
                modality="tts",
                target_category="tts",
                language=lang_model,
                confidence=0.95,
                is_neural=False,
                reason="High-signal speech synthesis keyword match"
            )

        # Neural System 1 Classification via Laya for natural language requests
        router = self._ensure_router()
        if router is not None:
            try:
                questions = {
                    "category": {
                        "type": "choice",
                        "instructions": "Which specialized model category is needed to fulfill this request?",
                        "criteria": {
                            "vision": "requires image, picture, photo, screenshot, diagram, visual inspection, viewing, finding, generating or creating an image",
                            "asr": "requires speech to text transcription or listening to audio",
                            "tts": "requires text to speech, reading aloud, or voice output",
                            "llm": "requires text conversation, general reasoning, programming, writing code, or answering questions"
                        }
                    }
                }
                res = router.predict(q_clean, questions)
                ans = res.get("answers", {}).get("category", {})
                choice = ans.get("choice", "llm")
                conf = float(ans.get("answer_confidence", ans.get("confidence", 0.9)))
                probs = ans.get("probabilities", {})

                modality = "coding" if any(k in q_lower for k in ("def ", "code", "python", "script", "bug", "error")) else ("chat" if choice == "llm" else choice)

                return IntentDecision(
                    modality=modality,
                    target_category=choice,
                    language=lang_model,
                    confidence=conf,
                    probabilities=probs,
                    is_neural=True,
                    reason=f"Neural decision by Laya ({choice})"
                )
            except Exception as e:
                logger.warning("Laya classify_intent fallback: %s", e)

        # Resilient default fallback
        modality = "coding" if any(k in q_lower for k in ("def ", "code", "python", "script", "function", "class ", "bug", "error")) else "chat"
        return IntentDecision(
            modality=modality,
            target_category="llm",
            language=lang_model,
            confidence=0.85,
            is_neural=False,
            reason="Default LLM fallback"
        )

    def verify_response(
        self,
        user_query: str,
        assistant_reply: str,
        threshold: float = 0.20
    ) -> ResponseVerification:
        """
        Post-LLM Decision Gate:
        Evaluates (User Query, Assistant Response) to detect topic drift,
        hallucination, or repetitive topic-locking.
        """
        user_clean = (user_query or "").strip()
        reply_clean = (assistant_reply or "").strip()

        if not user_clean or not reply_clean:
            return ResponseVerification(
                is_valid=True,
                addresses_query=True,
                confidence=1.0,
                drift_detected=False,
                reason="Trivial empty sequence"
            )

        router = self._ensure_router()
        if router is not None:
            try:
                state = {
                    "user_query": user_clean,
                    "assistant_reply": reply_clean
                }
                questions = {
                    "addresses_query": {
                        "type": "noul",
                        "instructions": "Does the assistant reply directly address the user query?"
                    }
                }
                res = router.predict(state, questions)
                ans = res.get("answers", {}).get("addresses_query", {})
                prob = float(ans.get("noul", 0.5))

                addresses = prob >= threshold
                drift = prob < threshold

                return ResponseVerification(
                    is_valid=addresses,
                    addresses_query=addresses,
                    confidence=prob,
                    drift_detected=drift,
                    addresses_prob=prob,
                    reason=f"Laya neural verification score: {prob:.4f}",
                    is_neural=True
                )
            except Exception as e:
                logger.warning("Laya verify_response fallback: %s", e)

        # Heuristic fallback: simple word overlap check
        u_words = set(re.findall(r"\w{4,}", user_clean.lower()))
        r_words = set(re.findall(r"\w{4,}", reply_clean.lower()))
        overlap = len(u_words & r_words)

        is_valid = True
        drift = False
        if len(u_words) >= 3 and overlap == 0 and len(reply_clean) > 300:
            drift = True
            is_valid = False

        return ResponseVerification(
            is_valid=is_valid,
            addresses_query=is_valid,
            confidence=0.75,
            drift_detected=drift,
            addresses_prob=0.75 if is_valid else 0.1,
            reason="Heuristic word overlap fallback",
            is_neural=False
        )

    def evaluate_tool_safety(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolSafetyDecision:
        """
        Evaluates risk score of proposed tool actions.
        """
        # Read-only and non-destructive tools are unconditionally safe
        safe_tools = {
            "read_file", "read_text_file", "read_multiple_files",
            "list_dir", "list_directory", "grep_search", "search_files",
            "get_file_info", "view_file", "search_web", "read_url_content",
            "knowledge_search", "obsidian_search", "system_status"
        }
        if tool_name in safe_tools:
            return ToolSafetyDecision(
                is_allowed=True,
                risk_level="safe",
                confidence=1.0,
                reason="Read-only tool",
                is_neural=False
            )

        cmd_str = str(arguments.get("command", arguments.get("CommandLine", "")))

        # Dangerous command patterns
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"format\s+[c-z]:",
            r"del\s+.*system32",
            r"rmdir\s+/s\s+/q\s+c:\\windows",
            r"drop\s+database",
            r":\(\)\{ :\|:& \};:"
        ]
        for pat in dangerous_patterns:
            if re.search(pat, cmd_str, re.IGNORECASE):
                return ToolSafetyDecision(
                    is_allowed=False,
                    risk_level="dangerous",
                    confidence=1.0,
                    reason="Blocked destructive shell command pattern",
                    is_neural=False
                )

        router = self._ensure_router()
        if router is not None:
            try:
                state = {
                    "tool": tool_name,
                    "arguments": arguments
                }
                questions = {
                    "risk": {
                        "type": "choice",
                        "instructions": "Assess the risk level of executing this system action",
                        "criteria": {
                            "safe": "benign read, localized test run, or standard status check",
                            "caution": "modifies local file, builds project, or installs packages",
                            "dangerous": "deletes system files, formats disks, kills critical processes"
                        }
                    }
                }
                res = router.predict(state, questions)
                choice = res.get("answers", {}).get("risk", {}).get("choice", "caution")
                conf = float(res.get("answers", {}).get("risk", {}).get("answer_confidence", 0.9))

                return ToolSafetyDecision(
                    is_allowed=choice != "dangerous",
                    risk_level=choice,
                    confidence=conf,
                    reason=f"Laya safety evaluation: {choice}",
                    is_neural=True
                )
            except Exception as e:
                logger.warning("Laya evaluate_tool_safety fallback: %s", e)

        return ToolSafetyDecision(
            is_allowed=True,
            risk_level="caution",
            confidence=0.8,
            reason="Heuristic safety evaluation (action permitted under caution)",
            is_neural=False
        )

    def predict(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Dict[str, Any],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generic forward-pass prediction endpoint exposing Laya directly to any subagent.
        """
        router = self._ensure_router()
        if router is None:
            raise RuntimeError("Laya Decision Engine is not available.")

        kwargs = {}
        if model:
            kwargs["model"] = model

        return router.predict(state, questions, **kwargs)

    def select_suitable_model(
        self,
        query: str,
        task_type: str = "auto",
        has_image: bool = False,
        has_audio: bool = False,
        candidates: Optional[List[Dict[str, Any]]] = None,
        cloud_providers: Optional[List[Dict[str, Any]]] = None,
        running_model_path: Optional[str] = None,
    ):
        """
        Selects the best model (local or cloud) based on task demands and model capabilities.
        """
        from laya_model_selector import laya_model_selector
        laya_model_selector._decision_engine = self
        return laya_model_selector.select_best_model(
            query=query,
            task_type=task_type,
            has_image=has_image,
            has_audio=has_audio,
            candidates=candidates,
            cloud_providers=cloud_providers,
            running_model_path=running_model_path,
        )

    def evaluate_browsing_need(self, query: str):
        """
        Evaluates whether a user query requires live web search or external browsing.
        """
        from laya_browsing import laya_browsing
        laya_browsing._decision_engine = self
        return laya_browsing.evaluate_browsing_need(query)

    def select_browsing_action(
        self,
        objective: str,
        current_url: str,
        elements: List[Dict[str, Any]],
    ):
        """
        Selects the next optimal DOM element to interact with during browsing.
        """
        from laya_browsing import laya_browsing
        laya_browsing._decision_engine = self
        return laya_browsing.select_browsing_action(objective, current_url, elements)

    def verify_browsing_content(
        self,
        objective: str,
        content: str,
        current_url: str = "",
    ):
        """
        Verifies whether retrieved webpage content fulfills the research objective.
        """
        from laya_browsing import laya_browsing
        laya_browsing._decision_engine = self
        return laya_browsing.verify_browsing_content(objective, content, current_url)


# Global singleton instance
decision_engine = DecisionEngine()

