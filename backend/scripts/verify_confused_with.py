"""
Verification Script for CONFUSED_WITH Relationships

Checks Neo4j for CONFUSED_WITH relationships and reports statistics.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_connection import Neo4jConnection


def verify_confused_with_relationships():
    """Verify CONFUSED_WITH relationships in Neo4j."""
    print("=" * 60)
    print("CONFUSED_WITH Relationships Verification")
    print("=" * 60)
    
    try:
        conn = Neo4jConnection()
        
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            return False
        
        print("✅ Connected to Neo4j\n")
        
        with conn.get_session() as session:
            # 1. Count total relationships
            count_query = """
                MATCH ()-[r:CONFUSED_WITH]->()
                RETURN count(r) as total
            """
            result = session.run(count_query)
            total = result.single()["total"]
            print(f"📊 Total CONFUSED_WITH relationships: {total}")
            
            if total == 0:
                print("⚠️  WARNING: No CONFUSED_WITH relationships found!")
                print("   Run adversary_builder.py to create relationships.")
                return False
            
            # 2. Count by reason
            reason_query = """
                MATCH ()-[r:CONFUSED_WITH]->()
                RETURN r.reason as reason, count(r) as count
                ORDER BY count DESC
            """
            result = session.run(reason_query)
            print("\n📈 Relationships by reason:")
            for record in result:
                print(f"   - {record['reason']}: {record['count']}")
            
            # 3. Sample relationships
            sample_query = """
                MATCH (source:Word)-[r:CONFUSED_WITH]->(target:Word)
                RETURN source.name as source_word,
                       target.name as target_word,
                       r.reason as reason,
                       r.distance as distance,
                       r.source as source
                LIMIT 10
            """
            result = session.run(sample_query)
            records = list(result)
            
            print("\n📋 Sample relationships:")
            for record in records:
                print(f"   {record['source_word']} -[:CONFUSED_WITH {{reason: '{record['reason']}', distance: {record['distance']}}}]-> {record['target_word']}")
            
            # 4. Words with most relationships
            top_words_query = """
                MATCH (w:Word)-[:CONFUSED_WITH]->(other:Word)
                RETURN w.name as word, w.frequency_rank as rank, count(other) as count
                ORDER BY count DESC
                LIMIT 10
            """
            result = session.run(top_words_query)
            records = list(result)
            
            print("\n🏆 Words with most CONFUSED_WITH relationships:")
            for record in records:
                print(f"   - {record['word']} (rank {record['rank']}): {record['count']} relationships")
            
            # 5. Check for common words (rank < 2000)
            common_words_query = """
                MATCH (w:Word)-[:CONFUSED_WITH]->(other:Word)
                WHERE w.frequency_rank < 2000
                RETURN count(DISTINCT w) as word_count
            """
            result = session.run(common_words_query)
            common_count = result.single()["word_count"]
            print(f"\n📚 Common words (rank < 2000) with relationships: {common_count}")
            
            # 6. Verify properties
            print("\n🔍 Verifying relationship properties...")
            prop_check_query = """
                MATCH ()-[r:CONFUSED_WITH]->()
                WHERE r.reason IS NULL OR r.distance IS NULL OR r.source IS NULL
                RETURN count(r) as missing_props
            """
            result = session.run(prop_check_query)
            missing = result.single()["missing_props"]
            
            if missing > 0:
                print(f"   ⚠️  WARNING: {missing} relationships missing required properties")
            else:
                print("   ✅ All relationships have required properties")
            
            print("\n" + "=" * 60)
            print("✅ Verification complete!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    success = verify_confused_with_relationships()
    sys.exit(0 if success else 1)


