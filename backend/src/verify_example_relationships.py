"""
Verification Script: Example Relationship Accuracy

Verifies that Stage 2 examples correctly use relationship words:
- Layer 2 examples contain words from OPPOSITE_TO relationships
- Layer 3 examples contain words from RELATED_TO relationships
- Layer 4 examples contain words from CONFUSED_WITH relationships
"""

import json
from src.database.neo4j_connection import Neo4jConnection


def verify_relationship_accuracy(conn: Neo4jConnection):
    """Verify that examples correctly use relationship words."""
    print("=" * 60)
    print("STAGE 2: EXAMPLE RELATIONSHIP ACCURACY CHECK")
    print("=" * 60)
    
    with conn.get_session() as session:
        # Get senses with Stage 2 enrichment
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.stage2_enriched = true
            RETURN w.name as word, s.id as sense_id,
                   s.examples_opposite as opposite_examples,
                   s.examples_similar as similar_examples,
                   s.examples_confused as confused_examples
            LIMIT 10
        """)
        
        records = list(result)
        if not records:
            print("❌ No Stage 2 enriched senses found.")
            return
        
        print(f"Checking {len(records)} enriched senses...\n")
        
        issues = []
        passed = 0
        
        for record in records:
            word = record["word"]
            sense_id = record["sense_id"]
            # Parse JSON strings if they exist
            opposite_raw = record.get("opposite_examples") or "[]"
            similar_raw = record.get("similar_examples") or "[]"
            confused_raw = record.get("confused_examples") or "[]"
            
            opposite_examples = json.loads(opposite_raw) if isinstance(opposite_raw, str) else (opposite_raw or [])
            similar_examples = json.loads(similar_raw) if isinstance(similar_raw, str) else (similar_raw or [])
            confused_examples = json.loads(confused_raw) if isinstance(confused_raw, str) else (confused_raw or [])
            
            # Fetch actual relationships
            rel_result = session.run("""
                MATCH (w:Word {name: $word})
                OPTIONAL MATCH (w)-[:OPPOSITE_TO]->(opp:Word)
                OPTIONAL MATCH (w)-[:RELATED_TO]->(sim:Word)
                OPTIONAL MATCH (w)-[r:CONFUSED_WITH]->(conf:Word)
                RETURN collect(DISTINCT opp.name) as opposites,
                       collect(DISTINCT sim.name) as similar,
                       collect(DISTINCT conf.name) as confused
            """, word=word)
            
            rel_data = rel_result.single()
            actual_opposites = set(rel_data["opposites"] or [])
            actual_similar = set(rel_data["similar"] or [])
            actual_confused = set(rel_data["confused"] or [])
            
            # Check Layer 2 (Opposites)
            for ex in opposite_examples:
                rel_word = ex.get("relationship_word", "").lower()
                example_text = ex.get("example_en", "").lower()
                
                if rel_word and rel_word not in actual_opposites:
                    issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "opposite",
                        "issue": f"Relationship word '{rel_word}' not in OPPOSITE_TO relationships",
                        "example": ex.get("example_en", "")[:80]
                    })
                elif rel_word and rel_word not in example_text:
                    issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "opposite",
                        "issue": f"Relationship word '{rel_word}' not found in example text",
                        "example": ex.get("example_en", "")[:80]
                    })
            
            # Check Layer 3 (Similar)
            for ex in similar_examples:
                rel_word = ex.get("relationship_word", "").lower()
                example_text = ex.get("example_en", "").lower()
                
                if rel_word and rel_word not in actual_similar:
                    issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "similar",
                        "issue": f"Relationship word '{rel_word}' not in RELATED_TO relationships",
                        "example": ex.get("example_en", "")[:80]
                    })
                elif rel_word and rel_word not in example_text:
                    issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "similar",
                        "issue": f"Relationship word '{rel_word}' not found in example text",
                        "example": ex.get("example_en", "")[:80]
                    })
            
            # Check Layer 4 (Confused)
            for ex in confused_examples:
                rel_word = ex.get("relationship_word", "").lower()
                example_text = ex.get("example_en", "").lower()
                
                if rel_word and rel_word not in actual_confused:
                    issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "confused",
                        "issue": f"Relationship word '{rel_word}' not in CONFUSED_WITH relationships",
                        "example": ex.get("example_en", "")[:80]
                    })
                elif rel_word and rel_word not in example_text:
                    issues.append({
                        "sense_id": sense_id,
                        "word": word,
                        "layer": "confused",
                        "issue": f"Relationship word '{rel_word}' not found in example text",
                        "example": ex.get("example_en", "")[:80]
                    })
            
            if not any([
                (opposite_examples and any(ex.get("relationship_word", "").lower() not in actual_opposites 
                                          or ex.get("relationship_word", "").lower() not in ex.get("example_en", "").lower()
                                          for ex in opposite_examples)),
                (similar_examples and any(ex.get("relationship_word", "").lower() not in actual_similar
                                         or ex.get("relationship_word", "").lower() not in ex.get("example_en", "").lower()
                                         for ex in similar_examples)),
                (confused_examples and any(ex.get("relationship_word", "").lower() not in actual_confused
                                          or ex.get("relationship_word", "").lower() not in ex.get("example_en", "").lower()
                                          for ex in confused_examples))
            ]):
                passed += 1
        
        # Report results
        print(f"✅ Passed: {passed}/{len(records)} senses")
        print(f"❌ Issues found: {len(issues)}\n")
        
        if issues:
            print("Issues:")
            for i, issue in enumerate(issues[:10], 1):  # Show first 10
                print(f"\n{i}. {issue['word']} ({issue['sense_id']}) - Layer: {issue['layer']}")
                print(f"   Issue: {issue['issue']}")
                print(f"   Example: {issue['example']}")
            
            if len(issues) > 10:
                print(f"\n... and {len(issues) - 10} more issues")
        else:
            print("✅ All relationship words correctly used in examples!")


if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            verify_relationship_accuracy(conn)
    finally:
        conn.close()

