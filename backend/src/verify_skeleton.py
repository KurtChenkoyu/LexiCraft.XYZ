"""
Verification Script for V6.1 Skeleton
Checks if Words are correctly connected to Senses.
"""

import sys
from pathlib import Path
from src.database.neo4j_connection import Neo4jConnection

def verify_skeleton(conn: Neo4jConnection):
    print("Verifying V6.1 Skeleton Graph...")
    
    with conn.get_session() as session:
        # 1. Check Words with Senses
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            RETURN count(DISTINCT w) as words_with_senses, count(s) as total_senses
        """)
        record = result.single()
        print(f"Words with Senses: {record['words_with_senses']}")
        print(f"Total Senses Created: {record['total_senses']}")
        
        # 2. Inspect a specific word (e.g., 'bank')
        print("\nInspecting 'bank' Skeleton:")
        result = session.run("""
            MATCH (w:Word {name: "bank"})-[:HAS_SENSE]->(s:Sense)
            RETURN s.id, s.pos, s.definition
            LIMIT 5
        """)
        for record in result:
            print(f"  [{record['s.id']}] ({record['s.pos']}): {record['s.definition'][:100]}...")

        # 3. Check for Orphans (Words without senses)
        result = session.run("""
            MATCH (w:Word)
            WHERE NOT (w)-[:HAS_SENSE]->()
            RETURN count(w) as orphan_count
        """)
        orphan_count = result.single()["orphan_count"]
        print(f"\nOrphan Words (No WordNet data): {orphan_count}")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_skeleton(conn)
    finally:
        conn.close()

