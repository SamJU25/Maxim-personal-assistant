"""
BrowserSkill CLI & Real-Session Browser Bridge for MaxIM.
Adapted from Tencent/BrowserSkill architecture.

This module re-exports BrowserSkillBridge and browser_skill_bridge from
backend.browser_agent to preserve complete backward compatibility while
consolidating the browser architecture into a single unified engine.
"""
from browser_agent import BrowserSkillBridge, browser_skill_bridge

__all__ = ["BrowserSkillBridge", "browser_skill_bridge"]
