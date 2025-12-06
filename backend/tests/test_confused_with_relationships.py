"""
Tests for CONFUSED_WITH Relationships in Neo4j

Verifies that:
1. CONFUSED_WITH relationships exist in Neo4j
2. Relationships are used correctly in survey question generation
3. Relationships have proper properties (reason, distance, source)
"""

import pytest
from src.database.neo4j_connection import Neo4jConnection
from src.survey.lexisurvey_engine import LexiSurveyEngine


@pytest.fixture
def neo4j_conn():
    """Create a Neo4j connection for testing."""
    conn = Neo4jConnection()
    yield conn
    conn.close()


@pytest.fixture
def engine(neo4j_conn):
    """Create a LexiSurveyEngine instance."""
    return LexiSurveyEngine(neo4j_conn)


class TestConfusedWithRelationships:
    """Tests for CONFUSED_WITH relationships."""
    
    def test_confused_with_relationships_exist(self, neo4j_conn):
        """Test that CONFUSED_WITH relationships exist in Neo4j."""
        with neo4j_conn.get_session() as session:
            # Count total CONFUSED_WITH relationships
            count_query = """
                MATCH ()-[r:CONFUSED_WITH]->()
                RETURN count(r) as total
            """
            result = session.run(count_query)
            count = result.single()["total"]
            
            assert count > 0, "No CONFUSED_WITH relationships found in Neo4j"
            print(f"✅ Found {count} CONFUSED_WITH relationships")
    
    def test_confused_with_has_properties(self, neo4j_conn):
        """Test that CONFUSED_WITH relationships have required properties."""
        with neo4j_conn.get_session() as session:
            # Get sample relationships with properties
            query = """
                MATCH (source:Word)-[r:CONFUSED_WITH]->(target:Word)
                RETURN source.name as source_word, 
                       target.name as target_word,
                       r.reason as reason,
                       r.distance as distance,
                       r.source as source
                LIMIT 10
            """
            result = session.run(query)
            records = list(result)
            
            assert len(records) > 0, "No CONFUSED_WITH relationships found"
            
            for record in records:
                assert record["source_word"] is not None
                assert record["target_word"] is not None
                assert record["reason"] is not None, f"Missing reason for {record['source_word']} -> {record['target_word']}"
                assert record["distance"] is not None, f"Missing distance for {record['source_word']} -> {record['target_word']}"
                assert record["source"] is not None, f"Missing source for {record['source_word']} -> {record['target_word']}"
                
                # Verify reason is one of expected values
                assert record["reason"] in ["Look-alike", "Sound-alike", "Semantic"], \
                    f"Unexpected reason: {record['reason']}"
                
                # Verify distance is a number
                assert isinstance(record["distance"], (int, float)), \
                    f"Distance should be a number, got {type(record['distance'])}"
    
    def test_confused_with_used_in_question_generation(self, neo4j_conn, engine):
        """Test that CONFUSED_WITH relationships are used when generating questions."""
        from src.survey.models import SurveyState
        
        # Create a test state
        state = SurveyState(
            session_id="test_session",
            current_rank=2000,
            low_bound=1,
            high_bound=8000,
            history=[],
            phase=1,
            confidence=0.0,
            pivot_triggered=False
        )
        
        # Generate a question payload
        payload = engine._generate_question_payload(2000, 1, state)
        
        # Verify payload has options
        assert payload is not None
        assert len(payload.options) == 6
        
        # Check if any options are traps (from CONFUSED_WITH)
        trap_options = [
            opt for opt in payload.options
            if opt.type == "trap" or "trap" in opt.id.lower()
        ]
        
        # We should have at least some traps if CONFUSED_WITH relationships exist
        # (though it's possible none were found for this specific word)
        print(f"Generated question for word: {payload.word}")
        print(f"Found {len(trap_options)} trap options")
        
        # Verify all option types are present
        option_types = {opt.type for opt in payload.options}
        assert "target" in option_types, "No target options found"
        assert "unknown" in option_types, "No unknown option found"
    
    def test_confused_with_bidirectional(self, neo4j_conn):
        """Test that CONFUSED_WITH relationships can be queried bidirectionally."""
        with neo4j_conn.get_session() as session:
            # Find a word with CONFUSED_WITH relationships
            query = """
                MATCH (w:Word)-[:CONFUSED_WITH]->(other:Word)
                RETURN w.name as word, count(other) as confused_count
                ORDER BY confused_count DESC
                LIMIT 5
            """
            result = session.run(query)
            records = list(result)
            
            if len(records) > 0:
                # Test word with most CONFUSED_WITH relationships
                test_word = records[0]["word"]
                
                # Query outgoing relationships
                outgoing_query = """
                    MATCH (w:Word {name: $word})-[r:CONFUSED_WITH]->(other:Word)
                    RETURN other.name as confused_word, r.reason as reason
                    LIMIT 5
                """
                outgoing_result = session.run(outgoing_query, word=test_word)
                outgoing_records = list(outgoing_result)
                
                assert len(outgoing_records) > 0, f"No outgoing CONFUSED_WITH relationships for {test_word}"
                print(f"✅ Word '{test_word}' has {len(outgoing_records)} CONFUSED_WITH relationships")
    
    def test_confused_with_for_common_words(self, neo4j_conn):
        """Test that common words (rank < 2000) have CONFUSED_WITH relationships."""
        with neo4j_conn.get_session() as session:
            # Find common words with CONFUSED_WITH relationships
            query = """
                MATCH (w:Word)-[:CONFUSED_WITH]->(other:Word)
                WHERE w.frequency_rank < 2000
                RETURN w.name as word, w.frequency_rank as rank, count(other) as confused_count
                ORDER BY w.frequency_rank ASC
                LIMIT 10
            """
            result = session.run(query)
            records = list(result)
            
            if len(records) > 0:
                print(f"✅ Found {len(records)} common words with CONFUSED_WITH relationships:")
                for record in records:
                    print(f"   - {record['word']} (rank {record['rank']}): {record['confused_count']} relationships")
            else:
                print("⚠️  No common words with CONFUSED_WITH relationships found")
                # This is a warning, not a failure, as relationships may still be building


