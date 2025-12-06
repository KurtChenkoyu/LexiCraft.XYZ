"""
Test script for learning point population.

Tests the population script with a small sample of words.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.database.neo4j_connection import Neo4jConnection
from src.database.neo4j_crud.learning_points import (
    get_learning_point,
    get_learning_point_by_word,
    list_learning_points,
    delete_learning_point
)
from scripts.populate_learning_points import (
    create_learning_points_for_word,
    normalize_word,
    generate_id,
    get_word_synsets
)
import nltk
from nltk.corpus import wordnet as wn

# Download NLTK data if needed
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)


# Test words (common words that should have WordNet data)
TEST_WORDS = [
    "beat",
    "book",
    "run",
    "time",
    "good",
    "make",
    "take",
    "come",
    "get",
    "go"
]


@pytest.fixture(scope="module")
def conn():
    """Create Neo4j connection for testing."""
    try:
        conn = Neo4jConnection()
        if not conn.verify_connectivity():
            pytest.skip("Neo4j connection not available")
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"Neo4j connection failed: {e}")


@pytest.fixture(scope="function")
def clean_test_data(conn):
    """Clean up test data before and after test."""
    # Clean up before test
    for word in TEST_WORDS:
        # Get all learning points for this word
        learning_points = list_learning_points(conn, limit=1000)
        for lp in learning_points:
            if lp.get('word') == word:
                delete_learning_point(conn, lp['id'])
    
    yield
    
    # Clean up after test
    for word in TEST_WORDS:
        learning_points = list_learning_points(conn, limit=1000)
        for lp in learning_points:
            if lp.get('word') == word:
                delete_learning_point(conn, lp['id'])


def test_normalize_word():
    """Test word normalization."""
    assert normalize_word("beat") == "beat"
    assert normalize_word("Beat Around The Bush") == "beat_around_the_bush"
    assert normalize_word("well-known") == "well_known"
    assert normalize_word("  test  ") == "test"


def test_generate_id():
    """Test ID generation."""
    assert generate_id("beat", "v", 1, 0) == "beat_v1"
    assert generate_id("beat", "n", 1, 0) == "beat_n1"
    assert generate_id("beat", "v", 2, 0) == "beat_v2"  # First Tier 2 meaning
    assert generate_id("beat", "v", 2, 1) == "beat_v3"  # Second Tier 2 meaning
    assert generate_id("beat", "n", 2, 0) == "beat_n2"  # First Tier 2 noun meaning


def test_get_word_synsets():
    """Test synset retrieval."""
    synsets = get_word_synsets("beat")
    assert len(synsets) > 0
    assert 'v' in synsets or 'n' in synsets  # Should have at least verb or noun


def test_create_learning_points_for_word(conn, clean_test_data):
    """Test creating learning points for a single word."""
    word = "beat"
    rank = 1
    
    tier1_count, tier2_count = create_learning_points_for_word(conn, word, rank, tier_limit=2)
    
    # Should create at least one Tier 1 learning point
    assert tier1_count > 0, f"Expected at least 1 Tier 1 learning point for '{word}'"
    
    # Verify learning points were created
    learning_points = list_learning_points(conn, limit=1000)
    beat_points = [lp for lp in learning_points if lp.get('word') == word]
    
    assert len(beat_points) >= tier1_count, "Not all Tier 1 points were created"
    
    # Verify Tier 1 point has correct properties
    tier1_points = [lp for lp in beat_points if lp.get('tier') == 1]
    assert len(tier1_points) == tier1_count
    
    for lp in tier1_points:
        assert lp['word'] == word
        assert lp['tier'] == 1
        assert lp['type'] == 'word'
        assert lp['definition'] is not None and len(lp['definition']) > 0
        assert lp['frequency_rank'] == rank
        assert lp['difficulty'] == 'B1'
        assert lp['register'] == 'both'
        assert 'id' in lp
        assert 'metadata' in lp
        assert 'pos' in lp['metadata']


def test_populate_sample_words(conn, clean_test_data):
    """Test populating a small sample of words."""
    words_processed = 0
    total_tier1 = 0
    total_tier2 = 0
    
    for word, rank in zip(TEST_WORDS, range(1, len(TEST_WORDS) + 1)):
        tier1, tier2 = create_learning_points_for_word(conn, word, rank, tier_limit=2)
        words_processed += 1
        total_tier1 += tier1
        total_tier2 += tier2
        
        # Each word should have at least one Tier 1 learning point
        assert tier1 > 0, f"Word '{word}' should have at least one Tier 1 learning point"
    
    # Verify total counts
    assert words_processed == len(TEST_WORDS)
    assert total_tier1 >= len(TEST_WORDS)  # At least one per word
    assert total_tier1 + total_tier2 > len(TEST_WORDS)  # Some words have multiple meanings
    
    # Verify in database
    all_points = list_learning_points(conn, limit=1000)
    test_points = [lp for lp in all_points if lp.get('word') in TEST_WORDS]
    
    assert len(test_points) == total_tier1 + total_tier2


def test_learning_point_data_quality(conn, clean_test_data):
    """Test data quality of created learning points."""
    word = "book"
    rank = 1
    
    tier1_count, tier2_count = create_learning_points_for_word(conn, word, rank, tier_limit=2)
    
    # Get all learning points for this word
    all_points = list_learning_points(conn, limit=1000)
    book_points = [lp for lp in all_points if lp.get('word') == word]
    
    # Verify no duplicates (unique IDs)
    ids = [lp['id'] for lp in book_points]
    assert len(ids) == len(set(ids)), "Duplicate IDs found"
    
    # Verify all have definitions
    for lp in book_points:
        assert lp['definition'] is not None
        assert len(lp['definition'].strip()) > 0, f"Empty definition for {lp['id']}"
        
        # Verify metadata structure
        assert 'metadata' in lp
        assert 'pos' in lp['metadata']
        assert 'synset_id' in lp['metadata']


def test_tier_1_only(conn, clean_test_data):
    """Test creating only Tier 1 learning points."""
    word = "run"
    rank = 1
    
    tier1_count, tier2_count = create_learning_points_for_word(conn, word, rank, tier_limit=1)
    
    assert tier1_count > 0
    assert tier2_count == 0  # Should not create Tier 2 when limit is 1
    
    # Verify only Tier 1 points exist
    all_points = list_learning_points(conn, limit=1000)
    run_points = [lp for lp in all_points if lp.get('word') == word]
    tier1_points = [lp for lp in run_points if lp.get('tier') == 1]
    tier2_points = [lp for lp in run_points if lp.get('tier') == 2]
    
    assert len(tier1_points) == tier1_count
    assert len(tier2_points) == 0


def test_word_without_wordnet(conn, clean_test_data):
    """Test handling of word without WordNet data."""
    # Use a very unlikely word or made-up word
    word = "xyzqwerty123"
    rank = 9999
    
    tier1_count, tier2_count = create_learning_points_for_word(conn, word, rank, tier_limit=2)
    
    # Should return 0 for both tiers
    assert tier1_count == 0
    assert tier2_count == 0
    
    # Verify no learning points were created
    all_points = list_learning_points(conn, limit=1000)
    word_points = [lp for lp in all_points if lp.get('word') == word]
    assert len(word_points) == 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

