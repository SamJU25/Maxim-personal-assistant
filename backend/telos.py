"""
LifeOS TELOS Engine for MaxIM.
Parses, updates, and enforces user intent and standards from Obsidian vault.
Framework: Daniel Miessler's TELOS (Targets, Execution, Lore, Operations, Stack).
"""
import re
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from config import config

class TELOSProfile(BaseModel):
    targets: List[str] = Field(default_factory=list)
    execution: List[str] = Field(default_factory=list)
    lore: List[str] = Field(default_factory=list)
    operations: List[str] = Field(default_factory=list)
    stack: List[str] = Field(default_factory=list)
    raw_content: str = ""

class LifeOSEngine:
    def __init__(self, telos_path: Optional[Path] = None):
        self.telos_path = telos_path or config.telos_path
        self._profile: Optional[TELOSProfile] = None

    def load(self) -> TELOSProfile:
        """Loads and parses the TELOS profile from the Obsidian vault."""
        if not self.telos_path.exists():
            return TELOSProfile()

        content = self.telos_path.read_text(encoding="utf-8")
        self._profile = self._parse_markdown(content)
        return self._profile

    def _parse_markdown(self, content: str) -> TELOSProfile:
        """Parses TELOS markdown headers into structured categories."""
        profile = TELOSProfile(raw_content=content)

        sections = re.split(r"^##\s+", content, flags=re.MULTILINE)
        for section in sections:
            lines = section.strip().split("\n")
            if not lines:
                continue
            header = lines[0].lower()
            body_items = [
                line.strip().lstrip("-* ").strip()
                for line in lines[1:]
                if line.strip().startswith(("-", "*"))
            ]

            if "target" in header:
                profile.targets.extend(body_items)
            elif "execution" in header:
                profile.execution.extend(body_items)
            elif "lore" in header:
                profile.lore.extend(body_items)
            elif "operation" in header:
                profile.operations.extend(body_items)
            elif "stack" in header:
                profile.stack.extend(body_items)

        return profile

    def get_context_injection(self) -> str:
        """
        Returns a token-budgeted markdown block of the user's LifeOS context
        to inject into the agent's system prompt.
        """
        profile = self.load()
        if not profile.targets and not profile.execution:
            return ""

        parts = ["### User LifeOS (TELOS Context)"]
        if profile.targets:
            parts.append("**Active Targets:** " + "; ".join(profile.targets[:4]))
        if profile.execution:
            parts.append("**Active Projects:** " + "; ".join(profile.execution[:4]))
        if profile.lore:
            parts.append("**Core Lore/Rules:** " + "; ".join(profile.lore[:3]))
        return "\n".join(parts)

    def add_target(self, target: str) -> bool:
        """Appends a new target milestone into the vault TELOS document."""
        if not self.telos_path.exists():
            return False

        content = self.telos_path.read_text(encoding="utf-8")
        target_line = f"- {target}\n"
        
        # Inject right after Targets section
        match = re.search(r"(##\s+.*?Targets.*?\n)", content, re.IGNORECASE)
        if match:
            idx = match.end()
            new_content = content[:idx] + target_line + content[idx:]
            self.telos_path.write_text(new_content, encoding="utf-8")
            self.load()
            return True
        return False

    def load_telos(self) -> TELOSProfile:
        """Alias for load()."""
        return self.load()

# Singleton instance
telos_engine = LifeOSEngine()

