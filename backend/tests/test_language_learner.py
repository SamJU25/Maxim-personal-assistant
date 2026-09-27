"""
Unit tests for MaxIM's Adaptive Language Acquisition Engine (Bangla, Chakma, Dialects).
Validates unvetted guess avoidance and script detection without invented meanings.
"""
import pytest
from pathlib import Path
from language_learner import LanguageLearner, LearnedPhrase

@pytest.fixture
def temp_learner(tmp_path: Path):
    db_file = tmp_path / "test_maxim_lang.db"
    return LanguageLearner(db_path=db_file)

def test_foundational_vocabulary_seeded(temp_learner):
    """Verify vetted Bangla vocabulary is seeded, while Chakma is not populated with guesses."""
    stats = temp_learner.get_learning_stats()
    assert stats["total_vocabulary"] >= 9
    assert "bangla" in stats["languages"]
    # Chakma must NOT be seeded with guessed meanings
    assert "chakma" not in stats["languages"]

    # Check specific foundational items
    ki_khobor = temp_learner.get_phrase("ki khobor")
    assert ki_khobor is not None
    assert ki_khobor.language == "bangla"
    assert ki_khobor.confidence == 1.0

def test_learn_new_phrase(temp_learner):
    """Verify manually or explicitly learning a new dialect phrase."""
    learned = temp_learner.learn_phrase(
        word_or_phrase="shunchen",
        language="bangla",
        meaning="Are you listening? (polite)",
        phonetic_script="শুনছেন",
        usage_example="Shunchen Sam, the tests passed.",
        confidence=0.95,
        source="user_taught",
    )
    assert learned.word_or_phrase == "shunchen"
    assert learned.times_heard == 1

    retrieved = temp_learner.get_phrase("shunchen")
    assert retrieved is not None
    assert retrieved.language == "bangla"
    assert retrieved.confidence == 0.95

def test_ingest_spoken_utterance_matches_known(temp_learner):
    """Verify spoken or chat utterances increment hearing counters for recognized phrases."""
    before_p = temp_learner.get_phrase("thik ache")
    initial_heard = before_p.times_heard

    res = temp_learner.ingest_spoken_utterance("Hey MaxIM, thik ache let's continue with this feature.")
    assert "thik ache" in res["matched_phrases"]

    after_p = temp_learner.get_phrase("thik ache")
    assert after_p.times_heard == initial_heard + 1

def test_ingest_spoken_utterance_extracts_taught_pattern(temp_learner):
    """Verify natural conversational pattern 'In Chakma, X means Y' teaches verified Chakma."""
    utterance = "Did you know that in Chakma, 'katha' means word or speech?"
    res = temp_learner.ingest_spoken_utterance(utterance)

    katha_p = temp_learner.get_phrase("katha")
    assert katha_p is not None
    assert katha_p.language == "chakma"
    assert "word" in katha_p.meaning.lower() or "speech" in katha_p.meaning.lower()
    assert katha_p.source == "user_taught"

def test_detect_scripts_without_inventing_vocabulary(temp_learner):
    """Verify Bengali and Chakma Unicode script detection logs matches without inventing meanings."""
    vocab_before = temp_learner.get_learning_stats()["total_vocabulary"]

    # Bengali script utterance
    res = temp_learner.ingest_spoken_utterance("এখানে কিছু বাংলা লিপি আছে।")
    assert any("[bengali-script]" in m for m in res["matched_phrases"])

    # Chakma script token (U+11100 block)
    res_chakma = temp_learner.ingest_spoken_utterance("Here is some Chakma: \U00011100\U00011101\U00011102")
    assert any("[chakma-script]" in m for m in res_chakma["matched_phrases"])

    # Crucial rule: script detection must NEVER create unvetted vocabulary or fake meanings
    vocab_after = temp_learner.get_learning_stats()["total_vocabulary"]
    assert vocab_after == vocab_before

def test_search_and_filter_vocabulary(temp_learner):
    """Verify search and dialect filtering after teaching."""
    temp_learner.learn_phrase(
        word_or_phrase="doi bhalo",
        language="chakma",
        meaning="Hello, are you well?",
        source="user_taught",
    )

    bangla_list = temp_learner.get_vocabulary(language="bangla")
    chakma_list = temp_learner.get_vocabulary(language="chakma")

    assert all(p.language == "bangla" for p in bangla_list)
    assert all(p.language == "chakma" for p in chakma_list)
    assert len(chakma_list) == 1
    assert chakma_list[0].word_or_phrase == "doi bhalo"

    search_res = temp_learner.search_vocabulary("bhalo")
    assert len(search_res) >= 2

def test_context_injection_format(temp_learner):
    """Verify system prompt context injection is well-structured and concise."""
    temp_learner.learn_phrase(
        word_or_phrase="doi bhalo",
        language="chakma",
        meaning="Hello, are you well?",
        source="user_taught",
    )
    injection = temp_learner.get_context_injection(limit=10)
    assert "Bangla" in injection
    assert "Chakma" in injection
    assert "ki khobor" in injection or "thik ache" in injection
    assert "doi bhalo" in injection

def test_record_usage(temp_learner):
    """Verify recording MaxIM using a phrase increments usage counter."""
    temp_learner.record_usage("ki khobor")
    phrase = temp_learner.get_phrase("ki khobor")
    assert phrase.times_used >= 1
