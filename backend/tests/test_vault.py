"""
Unit tests for Obsidian Vault Synapse (vault_tool.py).
Tests note reading, writing, search, backlink discovery, and path security.
"""
import pytest
from pathlib import Path
from tools.vault_tool import ObsidianVaultSynapse
from config import config

def test_read_real_vault_note():
    """Verify reading an existing note in the user's vault."""
    synapse = ObsidianVaultSynapse()
    res = synapse.read_note("Master MOC")
    
    assert res["found"] is True
    assert res["title"] == "Master MOC"
    assert "wikilinks" in res
    assert len(res["wikilinks"]) > 0
    assert any("DeepSeek" in w for w in res["wikilinks"])

def test_find_backlinks():
    """Verify finding notes that reference DeepSeek-V3 MoE Architecture."""
    synapse = ObsidianVaultSynapse()
    # Master MOC links to DeepSeek-V3 MoE Architecture
    backlinks = synapse.find_backlinks("DeepSeek-V3 MoE Architecture")
    
    assert len(backlinks) > 0
    sources = [b["source_title"] for b in backlinks]
    assert "Master MOC" in sources

def test_search_vault():
    """Verify keyword search returns relevant snippets."""
    synapse = ObsidianVaultSynapse()
    results = synapse.search_vault("galaxy")
    
    assert len(results) > 0
    titles = [r["title"] for r in results]
    assert any("Galaxy" in t or "MOC" in t for t in titles)

def test_write_and_read_note_isolated(tmp_path: Path):
    """Verify writing a note and reading it back with tags and wikilinks."""
    synapse = ObsidianVaultSynapse(vault_dir=tmp_path)
    
    write_res = synapse.write_note(
        title="Test Idea",
        content="Exploring [[DeepSeek-R1]] for agent loops.",
        folder="01 - Memory",
        tags=["#agent", "#research"]
    )
    assert write_res["status"] == "success"
    assert write_res["path"] == "01 - Memory/Test Idea.md"
    
    read_res = synapse.read_note("Test Idea")
    assert read_res["found"] is True
    assert "[[DeepSeek-R1]]" in read_res["content"]
    assert "#agent" in read_res["tags"]
    assert "#research" in read_res["tags"]
    assert read_res["wikilinks"] == ["DeepSeek-R1"]

def test_path_traversal_prevention(tmp_path: Path):
    """Verify path traversal outside vault is strictly blocked for folders, titles, and reads."""
    synapse = ObsidianVaultSynapse(vault_dir=tmp_path)
    res = synapse.write_note(
        title="Malicious",
        content="bad",
        folder="../../windows/system32"
    )
    assert "error" in res
    assert "prohibited" in res["error"].lower()

    # Title traversal prevention
    res_title = synapse.write_note(
        title="../../windows/system32/evil",
        content="bad",
        folder="01 - Memory"
    )
    assert "error" in res_title
    assert "prohibited" in res_title["error"].lower()

    # Read traversal prevention
    res_read = synapse.read_note("../../windows/system32/cmd.exe")
    assert res_read["found"] is False
