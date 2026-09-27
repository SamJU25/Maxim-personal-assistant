"""
backend/laya_browsing.py
========================
Laya-Driven Intelligent Browsing & Live Web Research Advisor.

Provides non-autoregressive System 1 decisions for:
1. Browsing Need Detection (determining if query requires live web search vs local knowledge)
2. Interactive Element Selection (choosing which DOM link, button, or search box to act on)
3. Content Sufficiency Verification (evaluating if fetched web page answers the objective)
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("maxim.laya_browsing")


@dataclass
class BrowsingDecision:
    needs_browsing: bool
    search_query: str
    confidence: float
    reason: str
    is_neural: bool = False


@dataclass
class BrowsingActionDecision:
    element_index: int
    action_type: str  # "click", "type", "extract", "done"
    suggested_value: str = ""
    confidence: float = 0.8
    reason: str = ""
    is_neural: bool = False


@dataclass
class BrowsingVerification:
    answers_objective: bool
    confidence: float
    key_findings: str = ""
    suggested_next_query: Optional[str] = None
    reason: str = ""
    is_neural: bool = False


class LayaBrowsingAdvisor:
    """
    MaxIM Laya Browsing Advisor.
    Guides the autonomous browser agent and reach tools using Laya decisions.
    """

    def __init__(self, decision_engine=None):
        self._decision_engine = decision_engine

    def evaluate_browsing_need(self, query: str) -> BrowsingDecision:
        """
        Determines if a user prompt requires live internet search or web browsing,
        and generates an optimized search keyword query.
        """
        q_clean = (query or "").strip()
        if not q_clean:
            return BrowsingDecision(
                needs_browsing=False,
                search_query="",
                confidence=1.0,
                reason="Empty input",
            )

        q_lower = q_clean.lower()

        # Explicit URL patterns
        url_match = re.search(r"https?://[^\s]+|www\.[^\s]+", q_clean)
        if url_match:
            return BrowsingDecision(
                needs_browsing=True,
                search_query=url_match.group(0),
                confidence=1.0,
                reason=f"Explicit web URL detected: {url_match.group(0)}",
            )

        # High-signal browsing and real-time query keywords
        browsing_triggers = (
            "search the web", "search online", "browse the web", "surf the web",
            "look up online", "google this", "duckduckgo", "latest news", "today's news",
            "current price", "stock price", "crypto price", "weather in", "recent developments",
            "what happened today", "who won", "live documentation", "github repository",
            "latest release", "latest version", "release date", "current version", "current release",
            "newest release", "changelog", "release notes", "what is the latest", "documentation for", "find online"
        )
        is_trigger_match = any(t in q_lower for t in browsing_triggers)

        # Try Laya neural router
        if self._decision_engine and self._decision_engine.is_available:
            try:
                questions = {
                    "needs_browsing": {
                        "type": "choice",
                        "instructions": "Does answering this request require searching the live internet or browsing external websites?",
                        "criteria": {
                            "yes": "asking about software releases, versions, recent news, current facts, weather, stock prices, external documentation, or browsing a website",
                            "no": "coding, mathematical derivation, creative writing, or general knowledge that does not require live web access"
                        }
                    }
                }
                res = self._decision_engine.predict(q_clean, questions)
                ans = res.get("answers", {}).get("needs_browsing", {})
                choice = ans.get("choice", "no")
                conf = float(ans.get("answer_confidence", ans.get("confidence", 0.85)))

                needs_browse = (choice == "yes") or is_trigger_match
                clean_q = self._clean_search_query(q_clean)

                return BrowsingDecision(
                    needs_browsing=needs_browse,
                    search_query=clean_q,
                    confidence=conf,
                    reason=f"Laya neural browsing decision ({choice})",
                    is_neural=True,
                )
            except Exception as e:
                logger.debug(f"Laya neural browsing evaluation fallback: {e}")

        clean_q = self._clean_search_query(q_clean)
        return BrowsingDecision(
            needs_browsing=is_trigger_match,
            search_query=clean_q,
            confidence=0.85 if is_trigger_match else 0.70,
            reason="Heuristic keyword trigger evaluation" if is_trigger_match else "Default local reasoning (no web search needed)",
            is_neural=False,
        )

    def select_browsing_action(
        self,
        objective: str,
        current_url: str,
        elements: List[Dict[str, Any]],
    ) -> BrowsingActionDecision:
        """
        Evaluates a page's interactive element tree to select the next optimal action
        (click relevant link/button, type in search box, or extract text).
        """
        if not elements:
            return BrowsingActionDecision(
                element_index=0,
                action_type="extract",
                confidence=1.0,
                reason="No interactive elements; recommend extracting page text content.",
            )

        obj_lower = (objective or "").lower()
        keywords = set(re.findall(r"\w{3,}", obj_lower))

        best_score = -1.0
        best_elem: Optional[Dict[str, Any]] = None
        action_type = "click"

        # Search box preference if query terms suggest searching
        is_searching = any(k in obj_lower for k in ("search", "find", "query", "look for"))

        for el in elements:
            score = 0.0
            el_type = str(el.get("element_type", el.get("tag", ""))).lower()
            text = str(el.get("text", "")).lower()
            name = str(el.get("name", "")).lower()
            placeholder = str(el.get("placeholder", "")).lower()
            href = str(el.get("href", "")).lower()

            combined = f"{text} {name} {placeholder} {href}"

            # 1. Matching objective keywords
            matches = sum(1 for kw in keywords if kw in combined)
            score += matches * 2.0

            # 2. Search inputs
            if is_searching and ("input" in el_type or "text" in el_type or "search" in combined):
                if any(s in combined for s in ("search", "query", "q", "find", "input")):
                    score += 5.0
                    action_type = "type"

            # 3. Relevant navigation links
            if el_type in ("link", "button", "a"):
                if any(nav in combined for nav in ("documentation", "docs", "guide", "pricing", "download", "readme", "article")):
                    score += 1.5

            if score > best_score:
                best_score = score
                best_elem = el

        if best_elem and best_score > 0.5:
            elem_idx = int(best_elem.get("index", 1))
            display_text = best_elem.get("text") or best_elem.get("name") or best_elem.get("placeholder") or "element"
            return BrowsingActionDecision(
                element_index=elem_idx,
                action_type=action_type,
                suggested_value=self._clean_search_query(objective) if action_type == "type" else "",
                confidence=min(1.0, 0.6 + (best_score * 0.1)),
                reason=f"Laya selected [{elem_idx}] '{display_text}' (score: {best_score:.1f}) matching objective",
                is_neural=False,
            )

        # Default fallback: extract text if already on page, or click first link
        return BrowsingActionDecision(
            element_index=1,
            action_type="extract",
            confidence=0.7,
            reason="Laya recommends reading page text to find answer.",
            is_neural=False,
        )

    def verify_browsing_content(
        self,
        objective: str,
        content: str,
        current_url: str = "",
    ) -> BrowsingVerification:
        """
        Verifies whether retrieved web content satisfies the research objective
        and extracts key findings.
        """
        obj_clean = (objective or "").strip()
        body_clean = (content or "").strip()

        if not body_clean:
            return BrowsingVerification(
                answers_objective=False,
                confidence=1.0,
                key_findings="Webpage is empty or returned no readable text.",
                suggested_next_query=self._clean_search_query(obj_clean),
                reason="Empty page content.",
            )

        # Use Laya neural router verification if available
        if self._decision_engine and self._decision_engine.is_available:
            try:
                state = {
                    "research_objective": obj_clean,
                    "web_content_snippet": body_clean[:1200],
                }
                questions = {
                    "answers_objective": {
                        "type": "noul",
                        "instructions": "Does this webpage content provide the information needed to answer the research objective?",
                    }
                }
                res = self._decision_engine.predict(state, questions)
                ans = res.get("answers", {}).get("answers_objective", {})
                score = float(ans.get("noul", 0.5))

                answers = score >= 0.45
                findings = self._extract_key_sentences(obj_clean, body_clean)

                return BrowsingVerification(
                    answers_objective=answers,
                    confidence=score,
                    key_findings=findings,
                    suggested_next_query=None if answers else self._clean_search_query(obj_clean),
                    reason=f"Laya neural content verification score: {score:.2f}",
                    is_neural=True,
                )
            except Exception as e:
                logger.debug(f"Laya neural browsing content verification fallback: {e}")

        # Heuristic word overlap verification
        obj_words = set(re.findall(r"\w{4,}", obj_clean.lower()))
        content_lower = body_clean.lower()
        matches = [w for w in obj_words if w in content_lower]
        ratio = len(matches) / max(1, len(obj_words))

        answers = ratio >= 0.5 or (len(matches) >= 2 and len(body_clean) > 200)
        findings = self._extract_key_sentences(obj_clean, body_clean)

        return BrowsingVerification(
            answers_objective=answers,
            confidence=round(ratio, 2),
            key_findings=findings,
            suggested_next_query=None if answers else f"{self._clean_search_query(obj_clean)} details",
            reason=f"Keyword coverage verification ({len(matches)}/{len(obj_words)} terms matched)",
            is_neural=False,
        )

    def _clean_search_query(self, query: str) -> str:
        """Strips conversational noise to build an efficient web search query."""
        clean = re.sub(
            r"^(please\s+)?(can you\s+)?(search\s+(for\s+)?|find\s+(me\s+)?|browse\s+(to\s+)?|look\s+up\s+|what\s+is\s+|tell\s+me\s+about\s+)",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip()
        clean = re.sub(r"[?!.,;]+$", "", clean).strip()
        return clean or query

    def _extract_key_sentences(self, objective: str, content: str, max_sentences: int = 3) -> str:
        """Finds sentences in the web text that have the highest overlap with the objective."""
        sentences = re.split(r"(?<=[.!?])\s+", content)
        obj_words = set(re.findall(r"\w{4,}", objective.lower()))

        scored = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) < 25 or len(s_clean) > 300:
                continue
            s_words = set(re.findall(r"\w{4,}", s_clean.lower()))
            overlap = len(obj_words & s_words)
            if overlap > 0:
                scored.append((overlap, s_clean))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [s for _, s in scored[:max_sentences]]
        return "\n".join(top) if top else (content[:400] + "..." if len(content) > 400 else content)


# Global singleton advisor
laya_browsing = LayaBrowsingAdvisor()
