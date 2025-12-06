"""
Verification Script for V6.1 Content Enrichment
Checks if Senses are enriched with Chinese/Examples.
"""

import sys
from pathlib import Path
from src.database.neo4j_connection import Neo4jConnection

def verify_enrichment(conn: Neo4jConnection):
    print("Verifying Enriched Content...")
    
    with conn.get_session() as session:
        # Inspect 'bank' Senses
        result = session.run("""
            MATCH (w:Word {name: "bank"})-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
            RETURN s.definition_zh, s.example_en, s.example_zh
        """)
        
        records = list(result)
        if not records:
            print("❌ No enriched senses found for 'bank'.")
            return

        for i, record in enumerate(records, 1):
            print(f"\nSense #{i}:")
            print(f"  ZH Def: {record['s.definition_zh']}")
            print(f"  Example: {record['s.example_en']}")
            print(f"  ZH Ex: {record['s.example_zh']}")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_enrichment(conn)
    finally:
        conn.close()

