"""
Unit and integration tests for Scientific Skills Engine (K-Dense adaptation).
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from scientific_skills import ScientificSkillsEngine

@pytest.fixture
def temp_science():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_science.db"
    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True)
    engine = ScientificSkillsEngine(db_path=db_path, vault_dir=vault_dir)
    yield engine, tmp_dir, vault_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_search_arxiv(temp_science):
    engine, _, _ = temp_science
    papers = engine.search_arxiv(query="direct preference optimization", max_results=2, test_mode=True)
    assert len(papers) == 2
    assert "Direct Preference Optimization" in papers[0]["title"]
    assert "arxiv:2305.18290" in papers[0]["id"]
    assert papers[0]["doi_or_url"] is not None
    assert len(papers[0]["authors"]) >= 1

    # Verify saved to database
    saved = engine.list_saved_papers()
    assert len(saved) >= 2

def test_search_pubmed(temp_science):
    engine, _, _ = temp_science
    articles = engine.search_pubmed(query="CRISPR gene therapy", max_results=1, test_mode=True)
    assert len(articles) == 1
    assert "pmid:" in articles[0]["id"]
    assert articles[0]["source"] == "pubmed"
    assert "Smith JA" in articles[0]["authors"]

def test_lookup_pubchem_compound(temp_science):
    engine, _, _ = temp_science
    
    # 1. Test Caffeine
    caffeine = engine.lookup_pubchem_compound("caffeine", test_mode=True)
    assert caffeine["cid"] == 2519
    assert caffeine["molecular_formula"] == "C8H10N4O2"
    assert caffeine["molecular_weight"] == 194.19
    assert "1,3,7-trimethylpurine" in caffeine["iupac_name"]
    assert "CN1C=NC2" in caffeine["smiles"]

    # 2. Test Aspirin
    aspirin = engine.lookup_pubchem_compound("aspirin", test_mode=True)
    assert aspirin["cid"] == 2244
    assert aspirin["molecular_formula"] == "C9H8O4"
    assert aspirin["molecular_weight"] == 180.16

def test_synthesize_literature_review(temp_science):
    engine, _, vault_dir = temp_science
    
    dossier = engine.synthesize_literature_review(
        topic="Reinforcement_Learning_Alignment",
        test_mode=True
    )
    assert dossier["dossier_id"] is not None
    assert dossier["topic"] == "Reinforcement_Learning_Alignment"
    assert dossier["paper_count"] >= 2
    assert Path(dossier["vault_path"]).exists()

    content = Path(dossier["vault_path"]).read_text(encoding="utf-8")
    assert "# 🔬 Literature Review: Reinforcement_Learning_Alignment" in content
    assert "Executive Abstract" in content
    assert "Key Papers & Findings" in content
    assert "Comparative Methodological Analysis" in content
    assert "BibTeX References" in content
    assert "@article{" in content
