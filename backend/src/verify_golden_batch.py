"""
Verification Script: Golden Batch Results
Checks for Questions and Phrases created by the V6.1 Pipeline.
"""

from src.database.neo4j_connection import Neo4jConnection

def verify_golden_batch(conn):
    print("=" * 60)
    print("GOLDEN BATCH VERIFICATION")
    print("=" * 60)
    
    with conn.get_session() as session:
        # 1. Check Question Nodes
        result = session.run("""
            MATCH (q:Question)
            RETURN count(q) as count
        """)
        q_count = result.single()["count"]
        print(f"✅ Total Question Nodes: {q_count}")
        
        # Sample Question
        if q_count > 0:
            result = session.run("""
                MATCH (s:Sense)-[:VERIFIED_BY]->(q:Question)
                RETURN s.id, q.text, q.options, q.answer
                LIMIT 1
            """)
            record = result.single()
            if record:
                print(f"\nSample Question for {record['s.id']}:")
                print(f"  Q: {record['q.text']}")
                print(f"  Options: {record['q.options']}")
                print(f"  Answer: {record['q.answer']}")

        # 2. Check Phrase Nodes
        result = session.run("""
            MATCH (p:Phrase)
            RETURN count(p) as count
        """)
        p_count = result.single()["count"]
        print(f"\n✅ Total Phrase Nodes: {p_count}")
        
        # Sample Phrase Mapping
        if p_count > 0:
            result = session.run("""
                MATCH (p:Phrase)-[:MAPS_TO_SENSE]->(s:Sense)<-[:HAS_SENSE]-(w:Word)
                RETURN w.name, p.text, s.definition
                LIMIT 1
            """)
            record = result.single()
            if record:
                print(f"\nSample Phrase Mapping:")
                print(f"  Word: {record['w.name']}")
                print(f"  Phrase: '{record['p.text']}'")
                print(f"  Mapped to Sense: {record['s.definition'][:100]}...")

        # 3. Check Coverage (Words with Questions)
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)-[:VERIFIED_BY]->(q:Question)
            RETURN count(DISTINCT w) as covered_words
        """)
        w_count = result.single()["covered_words"]
        print(f"\n✅ Words with Questions: {w_count}")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_golden_batch(conn)
    finally:
        conn.close()

