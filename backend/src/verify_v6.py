"""
Verification Script for V6.1 Architecture
Checks if Word nodes are loaded with correct ranking.
"""

import sys
from pathlib import Path
from src.database.neo4j_connection import Neo4jConnection

def verify_db(conn: Neo4jConnection):
    print("Verifying V6.1 Data...")
    
    with conn.get_session() as session:
        # 1. Check total count
        result = session.run("MATCH (w:Word) RETURN count(w) as count")
        count = result.single()["count"]
        print(f"Total Words: {count}")
        
        # 2. Check 'bank' (Should be boosted)
        result = session.run("""
            MATCH (w:Word {name: "bank"}) 
            RETURN w.name, w.frequency_rank, w.moe_level, w.ngsl_rank
        """)
        record = result.single()
        if record:
            print(f"\nNode Check: {record['w.name']}")
            print(f"  Unified Rank: {record['w.frequency_rank']} (Should be < NGSL rank)")
            print(f"  MOE Level: {record['w.moe_level']}")
            print(f"  Original NGSL: {record['w.ngsl_rank']}")
        else:
            print("❌ 'bank' node not found.")
            
        # 3. Check Top 5 Priority Words
        print("\nTop 5 Priority Words (Lowest Unified Rank):")
        result = session.run("""
            MATCH (w:Word)
            RETURN w.name, w.frequency_rank
            ORDER BY w.frequency_rank ASC
            LIMIT 5
        """)
        for record in result:
            print(f"  {record['w.name']}: {record['w.frequency_rank']}")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_db(conn)
    finally:
        conn.close()

