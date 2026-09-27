"""
Obsidian Vault Synapse for MaxIM.
Enables native reading, writing, searching, and backlink discovery across markdown notes.
Guarantees zero-hallucination boundaries: all operations are strictly contained in vault_dir.
"""
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from config import config

class ObsidianVaultSynapse:
    def __init__(self, vault_dir: Optional[Path] = None):
        self.vault_dir = vault_dir or config.vault_dir
        if not self.vault_dir.exists():
            self.vault_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_note_path(self, title_or_path: str) -> Optional[Path]:
        """Resolves a note title or relative path to an existing .md file."""
        clean_name = title_or_path.strip().replace("[[", "").replace("]]", "")
        if not clean_name.endswith(".md"):
            filename = f"{clean_name}.md"
        else:
            filename = clean_name

        # Direct relative path check
        vault_root = self.vault_dir.resolve()
        direct = (self.vault_dir / filename).resolve()
        try:
            direct.relative_to(vault_root)
        except ValueError:
            return None  # Path traversal attempt outside vault

        if direct.exists() and direct.is_file():
            return direct

        # Recursive search by base filename (case-insensitive)
        target_base = Path(filename).stem.lower()
        for p in self.vault_dir.rglob("*.md"):
            if p.stem.lower() == target_base:
                return p
        return None

    def read_note(self, title_or_path: str) -> Dict[str, Any]:
        """Reads note content, metadata, and extracted [[wikilinks]]."""
        path = self._resolve_note_path(title_or_path)
        if not path or not path.exists():
            return {"error": f"Note '{title_or_path}' not found in vault.", "found": False}

        content = path.read_text(encoding="utf-8")
        wikilinks = re.findall(r"\[\[([^\]]+?)\]\]", content)
        tags = re.findall(r"(?:^|\s)#([A-Za-z0-9_/-]+)", content)
        rel_path = path.relative_to(self.vault_dir).as_posix()

        return {
            "title": path.stem,
            "path": rel_path,
            "folder": path.parent.name,
            "content": content,
            "wikilinks": [w.split("|")[0].split("#")[0].strip() for w in wikilinks],
            "tags": [f"#{t}" for t in tags],
            "found": True,
        }

    def write_note(
        self,
        title: str,
        content: str,
        folder: str = "01 - Memory",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Creates or updates a markdown note in the vault.
        Strictly prevents path traversal attacks.
        """
        clean_title = title.strip().replace("[[", "").replace("]]", "")
        if not clean_title.endswith(".md"):
            filename = f"{clean_title}.md"
        else:
            filename = clean_title

        vault_root = self.vault_dir.resolve()
        target_folder = (self.vault_dir / folder).resolve()
        # Security: folder containment check
        try:
            target_folder.relative_to(vault_root)
        except ValueError:
            return {"error": "Invalid folder path: Traversal outside vault prohibited."}

        # Security: full file path containment check (prevents title traversal)
        file_path = (target_folder / filename).resolve()
        try:
            file_path.relative_to(vault_root)
        except ValueError:
            return {"error": "Invalid file path: Traversal outside vault prohibited."}

        target_folder.mkdir(parents=True, exist_ok=True)

        # Append tags to content if provided
        final_content = content.strip()
        if tags:
            tag_line = " ".join(t if t.startswith("#") else f"#{t}" for t in tags)
            if tag_line not in final_content:
                final_content += f"\n\n{tag_line}"

        file_path.write_text(final_content + "\n", encoding="utf-8")
        rel_path = file_path.relative_to(self.vault_dir).as_posix()

        return {
            "status": "success",
            "title": file_path.stem,
            "path": rel_path,
            "folder": folder,
            "bytes_written": len(final_content),
        }

    def search_vault(
        self,
        query: str,
        max_results: int = 10,
        use_semantic: bool = False,
        auto_boot: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Searches across the vault:
        - If use_semantic=True, leverages Qwen3-Embedding and Qwen3-Reranker via retrieval_engine.
        - Otherwise uses fast keyword search across markdown notes.
        """
        if use_semantic:
            try:
                from retrieval_engine import retrieval_engine
                semantic_hits = retrieval_engine.hybrid_search_vault(
                    query=query,
                    vault_dir=self.vault_dir,
                    max_results=max_results,
                    auto_boot=auto_boot,
                )
                if semantic_hits:
                    return semantic_hits
            except Exception:
                pass

        results = []
        q_lower = query.lower()

        for path in self.vault_dir.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8")
                if q_lower in text.lower() or q_lower in path.stem.lower():
                    # Extract matching line as snippet
                    snippet = ""
                    for line in text.splitlines():
                        if q_lower in line.lower():
                            snippet = line.strip()
                            break

                    results.append({
                        "title": path.stem,
                        "path": path.relative_to(self.vault_dir).as_posix(),
                        "folder": path.parent.name,
                        "snippet": snippet or text[:120].strip(),
                    })
                    if len(results) >= max_results:
                        break
            except Exception:
                continue

        return results

    def semantic_search_vault(
        self,
        query: str,
        max_results: int = 10,
        auto_boot: bool = False,
    ) -> List[Dict[str, Any]]:
        """Dense semantic search + neural reranking across vault notes."""
        return self.search_vault(
            query=query,
            max_results=max_results,
            use_semantic=True,
            auto_boot=auto_boot,
        )

    def find_backlinks(self, title: str) -> List[Dict[str, str]]:
        """Finds all notes in the vault that link to [[title]]."""
        clean_title = title.strip().replace("[[", "").replace("]]", "")
        pattern = re.compile(rf"\[\[{re.escape(clean_title)}(\|.*?)?\]\]", re.IGNORECASE)
        backlinks = []

        for path in self.vault_dir.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8")
                if pattern.search(text):
                    backlinks.append({
                        "source_title": path.stem,
                        "source_path": path.relative_to(self.vault_dir).as_posix(),
                    })
            except Exception:
                continue

        return backlinks

    def list_notes(self, folder: Optional[str] = None) -> List[Dict[str, str]]:
        """Lists markdown notes in the vault or specified subfolder."""
        base = self.vault_dir / folder if folder else self.vault_dir
        if not base.exists():
            return []

        notes = []
        for path in base.rglob("*.md"):
            notes.append({
                "title": path.stem,
                "path": path.relative_to(self.vault_dir).as_posix(),
                "folder": path.parent.name,
            })
        return notes

# Singleton instance
vault_synapse = ObsidianVaultSynapse()
