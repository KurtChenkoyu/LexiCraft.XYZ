"""
Investigate senses missing Level 2 examples.
"""

from src.database.neo4j_connection import Neo4jConnection

def investigate_missing_senses():
    """Find and analyze senses missing Level 2 examples."""
    conn = Neo4jConnection()
    
    with conn.get_session() as session:
        # Find senses that should have Level 2 but don't
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true 
              AND (s.stage2_enriched IS NULL OR s.stage2_enriched = false)
            OPTIONAL MATCH (s)-[r1:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO|OPPOSITE_TO]->(s2:Sense)
            OPTIONAL MATCH (w)-[r2:OPPOSITE_TO|RELATED_TO|CONFUSED_WITH]->(w2:Word)
            WITH w, s, 
                 count(DISTINCT s2) + count(DISTINCT w2) as relationship_count
            RETURN w.name as word,
                   s.id as sense_id,
                   s.definition_en as definition_en,
                   s.definition_zh as definition_zh,
                   s.pos as pos,
                   s.enriched as enriched,
                   s.stage2_enriched as stage2_enriched,
                   s.level2_examples as level2_examples,
                   s.examples_contextual as examples_contextual,
                   s.examples_opposite as examples_opposite,
                   s.examples_similar as examples_similar,
                   s.examples_confused as examples_confused,
                   relationship_count,
                   w.frequency_rank as frequency_rank
            ORDER BY w.frequency_rank ASC
        """)
        
        records = list(result)
        
        print("=" * 80)
        print(f"INVESTIGATING {len(records)} SENSES MISSING LEVEL 2 EXAMPLES")
        print("=" * 80)
        
        if not records:
            print("✅ All senses have Level 2 examples!")
            return
        
        # Check for relationships
        print("\n📊 Checking relationship availability...")
        with conn.get_session() as session2:
            for record in records:
                word = record["word"]
                sense_id = record["sense_id"]
                
                # Check what relationships exist for this sense
                rel_result = session2.run("""
                    MATCH (s1:Sense {id: $sense_id})
                    OPTIONAL MATCH (s1)-[r1:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO|OPPOSITE_TO|CONFUSED_WITH]->(s2:Sense)
                    OPTIONAL MATCH (w1:Word {name: $word})-[r2:OPPOSITE_TO|RELATED_TO|CONFUSED_WITH]->(w2:Word)
                    RETURN 
                        count(DISTINCT s2) as sense_rels,
                        count(DISTINCT w2) as word_rels,
                        collect(DISTINCT type(r1)) as sense_rel_types,
                        collect(DISTINCT type(r2)) as word_rel_types
                """, sense_id=sense_id, word=word)
                
                rel_data = rel_result.single()
                sense_rels = rel_data["sense_rels"] if rel_data else 0
                word_rels = rel_data["word_rels"] if rel_data else 0
                
                print(f"\n{'='*80}")
                print(f"Word: {word}")
                print(f"Sense ID: {sense_id}")
                print(f"POS: {record['pos']}")
                print(f"Definition (EN): {record['definition_en']}")
                print(f"Definition (ZH): {record['definition_zh']}")
                print(f"Frequency Rank: {record['frequency_rank']}")
                print(f"\nStatus:")
                print(f"  - enriched: {record['enriched']}")
                print(f"  - stage2_enriched: {record['stage2_enriched']}")
                print(f"  - level2_examples: {record['level2_examples'] is not None}")
                print(f"  - examples_contextual: {record['examples_contextual'] is not None}")
                print(f"  - examples_opposite: {record['examples_opposite'] is not None}")
                print(f"  - examples_similar: {record['examples_similar'] is not None}")
                print(f"  - examples_confused: {record['examples_confused'] is not None}")
                print(f"\nRelationships:")
                print(f"  - Sense-level relationships: {sense_rels}")
                print(f"  - Word-level relationships: {word_rels}")
                if rel_data:
                    print(f"  - Sense rel types: {rel_data['sense_rel_types']}")
                    print(f"  - Word rel types: {rel_data['word_rel_types']}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total missing: {len(records)}")
        print(f"With relationships: {sum(1 for r in records if r['relationship_count'] > 0)}")
        print(f"Without relationships: {sum(1 for r in records if r['relationship_count'] == 0)}")
        
        # Check if any have partial data
        partial = []
        for r in records:
            has_any = any([
                r['level2_examples'] is not None,
                r['examples_contextual'] is not None,
                r['examples_opposite'] is not None,
                r['examples_similar'] is not None,
                r['examples_confused'] is not None
            ])
            if has_any:
                partial.append(r)
        
        if partial:
            print(f"\n⚠️  {len(partial)} senses have partial Level 2 data:")
            for r in partial:
                print(f"  - {r['word']} ({r['sense_id']})")

if __name__ == "__main__":
    investigate_missing_senses()

