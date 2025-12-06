"""
Verification Script for V6.1 Adversarial Layer
Checks for Antonym and Synonym relationships between Words.
"""

import sys
from pathlib import Path
from src.database.neo4j_connection import Neo4jConnection

def verify_adversary(conn: Neo4jConnection):
    print("Verifying V6.1 Adversarial Layer...")
    
    with conn.get_session() as session:
        # 1. Check Total Relationship Counts
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        print("\nRelationship Counts:")
        for record in result:
            print(f"  {record['type']}: {record['count']}")
            
        # 2. Inspect Antonyms (OPPOSITE_TO)
        print("\nSample Antonyms (OPPOSITE_TO):")
        result = session.run("""
            MATCH (a:Word)-[:OPPOSITE_TO]->(b:Word)
            RETURN a.name, b.name
            LIMIT 5
        """)
        for record in result:
            print(f"  {record['a.name']} <--> {record['b.name']}")

        # 3. Inspect Synonyms (RELATED_TO)
        print("\nSample Synonyms (RELATED_TO):")
        result = session.run("""
            MATCH (a:Word)-[:RELATED_TO]->(b:Word)
            RETURN a.name, b.name
            LIMIT 5
        """)
        for record in result:
            print(f"  {record['a.name']} <--> {record['b.name']}")

        # 4. Specific Check for 'good' or 'big'
        target = "good"
        print(f"\nRelationships for '{target}':")
        result = session.run("""
            MATCH (w:Word {name: $word})-[r]-(other:Word)
            RETURN type(r) as type, other.name as neighbor
        """, word=target)
        for record in result:
            print(f"  {target} -[:{record['type']}]-> {record['neighbor']}")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_adversary(conn)
    finally:
        conn.close()

