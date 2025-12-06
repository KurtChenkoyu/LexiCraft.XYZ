#!/usr/bin/env python3
"""
Check status of relationship mining progress.
Run this while the relationship miner is running in the background.
"""

import sys
sys.path.insert(0, '.')
from src.database.neo4j_connection import Neo4jConnection

def check_status():
    conn = Neo4jConnection()
    session = conn.get_session()
    
    print("📊 Relationship Mining Status\n")
    
    # Check sense-level relationships
    result = session.run("""
        MATCH (s1:Sense)-[r]->(s2:Sense)
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY rel_type
    """)
    
    print("Sense-level relationships:")
    sense_total = 0
    for r in result:
        count = r["count"]
        sense_total += count
        print(f"  {r['rel_type']}: {count:,}")
    print(f"  Total: {sense_total:,}\n")
    
    # Check morphological relationships
    result = session.run("""
        MATCH (w1:Word)-[r:DERIVED_FROM|HAS_PREFIX|HAS_SUFFIX]->(w2:Word)
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY rel_type
    """)
    
    print("Morphological relationships:")
    morph_total = 0
    for r in result:
        count = r["count"]
        morph_total += count
        print(f"  {r['rel_type']}: {count:,}")
    print(f"  Total: {morph_total:,}\n")
    
    # Total relationships
    result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
    total = result.single()["total"]
    print(f"✅ Total relationships in graph: {total:,}")
    
    # Estimate progress (if we know target)
    print(f"\n📈 Progress:")
    print(f"  Relationship Milestone 1 (Sense relationships): {sense_total:,}")
    print(f"  Relationship Milestone 2 (Morphological): {morph_total:,}")
    print(f"  Combined: {sense_total + morph_total:,} new relationships")
    
    session.close()
    conn.close()

if __name__ == "__main__":
    check_status()

