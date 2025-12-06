"""
Verification Script: Content Quality Check
1. Chinese Translation Quality (Traditional Chinese, Taiwan naturalness)
2. Distractor Quality (Question nodes)
3. Phrase Mapping Accuracy (Phrase -> Sense relationships)
"""

from src.database.neo4j_connection import Neo4jConnection

def check_chinese_translations(conn):
    print("=" * 60)
    print("1. CHINESE TRANSLATION QUALITY CHECK")
    print("=" * 60)
    
    with conn.get_session() as session:
        # Get enriched senses with Chinese
        result = session.run("""
            MATCH (s:Sense)
            WHERE s.definition_zh IS NOT NULL
            RETURN s.id, s.definition_en, s.definition_zh, s.example_zh
            LIMIT 10
        """)
        
        records = list(result)
        if not records:
            print("❌ No Chinese translations found. Enrichment may not have run.")
            return
        
        print(f"Found {len(records)} enriched senses with Chinese.\n")
        
        for i, record in enumerate(records, 1):
            print(f"Example {i}:")
            print(f"  Sense ID: {record['s.id']}")
            print(f"  EN Def: {record['s.definition_en']}")
            print(f"  ZH Def: {record['s.definition_zh']}")
            print(f"  ZH Example: {record['s.example_zh']}")
            
            # Check for Traditional Chinese characters
            zh_text = record['s.definition_zh'] or ""
            # Traditional Chinese indicators (vs Simplified)
            traditional_indicators = ['繁體', '銀行', '他們', '這張']  # Common Traditional chars
            simplified_indicators = ['繁体', '银行', '他们', '这张']  # Simplified equivalents
            
            has_traditional = any(char in zh_text for char in traditional_indicators)
            has_simplified = any(char in zh_text for char in simplified_indicators)
            
            if has_traditional:
                print(f"  ✅ Contains Traditional Chinese characters")
            elif has_simplified:
                print(f"  ⚠️  Contains Simplified Chinese characters (may need review)")
            else:
                print(f"  ⚠️  Cannot determine script type")
            print()

def check_question_distractors(conn):
    print("=" * 60)
    print("2. DISTRACTOR QUALITY CHECK (Question Nodes)")
    print("=" * 60)
    
    with conn.get_session() as session:
        # Check if Question nodes exist
        result = session.run("""
            MATCH (q:Question)
            RETURN count(q) as count
        """)
        count = result.single()["count"]
        
        if count == 0:
            print("❌ No Question nodes found in database.")
            print("   Question generation may not have been implemented yet.")
            print("   (This is expected - Phase 2 Agent focuses on enrichment, not MCQ generation)")
            return
        
        print(f"Found {count} Question nodes.\n")
        
        # Sample questions
        result = session.run("""
            MATCH (q:Question)
            RETURN q.text, q.options, q.answer
            LIMIT 5
        """)
        
        for i, record in enumerate(result, 1):
            print(f"Question {i}:")
            print(f"  Text: {record['q.text']}")
            print(f"  Options: {record['q.options']}")
            print(f"  Correct Answer Index: {record['q.answer']}")
            
            # Analyze distractor quality
            options = record['q.options'] or []
            if len(options) >= 2:
                correct_idx = record['q.answer']
                wrong_options = [opt for idx, opt in enumerate(options) if idx != correct_idx]
                print(f"  Wrong Options: {wrong_options}")
                print(f"  ⚠️  Distractor quality: Manual review needed")
            print()

def check_phrase_mappings(conn):
    print("=" * 60)
    print("3. PHRASE MAPPING ACCURACY CHECK")
    print("=" * 60)
    
    with conn.get_session() as session:
        # Check if Phrase nodes exist
        result = session.run("""
            MATCH (p:Phrase)
            RETURN count(p) as count
        """)
        count = result.single()["count"]
        
        if count == 0:
            print("❌ No Phrase nodes found in database.")
            print("   Phrase extraction may not have been implemented yet.")
            print("   (This is expected - V6.1 Phase 1 focuses on words, phrases are Phase 2)")
            return
        
        print(f"Found {count} Phrase nodes.\n")
        
        # Check "run out of" specifically
        result = session.run("""
            MATCH (p:Phrase {text: "run out of"})-[:MAPS_TO_SENSE]->(s:Sense)
            MATCH (w:Word {name: "run"})-[:HAS_SENSE]->(s)
            RETURN s.id, s.definition, s.definition_en
        """)
        
        records = list(result)
        if not records:
            print("⚠️  'run out of' phrase not found, or not mapped to 'run' word.")
            print("   Checking all phrase mappings...\n")
            
            # General phrase check
            result = session.run("""
                MATCH (p:Phrase)-[:MAPS_TO_SENSE]->(s:Sense)
                MATCH (w:Word)-[:HAS_SENSE]->(s)
                RETURN p.text, w.name, s.id, s.definition
                LIMIT 10
            """)
            
            for record in result:
                print(f"  Phrase: '{record['p.text']}' -> Word: '{record['w.name']}'")
                print(f"    Sense: {record['s.id']}")
                print(f"    Definition: {record['s.definition'][:80]}...")
                print()
        else:
            print("Found 'run out of' mapping:\n")
            for record in records:
                print(f"  Phrase: 'run out of'")
                print(f"  Mapped to Sense: {record['s.id']}")
                print(f"  Definition: {record['s.definition']}")
                print(f"  Enriched Def: {record['s.definition_en']}")
                
                # Check if it's the "depletion" sense
                definition = record['s.definition'].lower()
                if 'deplet' in definition or 'exhaust' in definition or 'use up' in definition:
                    print(f"  ✅ Correctly mapped to Depletion sense")
                elif 'jog' in definition or 'run' in definition or 'move' in definition:
                    print(f"  ⚠️  May be mapped to Jogging/Movement sense (needs review)")
                print()

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            check_chinese_translations(conn)
            check_question_distractors(conn)
            check_phrase_mappings(conn)
    finally:
        conn.close()

