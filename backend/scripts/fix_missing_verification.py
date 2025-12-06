#!/usr/bin/env python3
"""
Fix enriched senses that are missing verification questions.
This script finds enriched senses without VERIFIED_BY relationships and creates questions for them.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection
from src.agent import get_enrichment, update_graph

def fix_missing_verification(conn: Neo4jConnection, target_word: str = None):
    """
    Find enriched senses missing verification questions and fix them.
    
    Args:
        conn: Neo4j connection
        target_word: Optional specific word to fix (e.g., "bank")
    """
    print("=" * 80)
    print("FIXING MISSING VERIFICATION QUESTIONS")
    print("=" * 80)
    print()
    
    with conn.get_session() as session:
        # Find enriched senses without verification questions
        if target_word:
            query = """
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true
                  AND NOT EXISTS((s)-[:VERIFIED_BY]->(:Question))
                RETURN w.name as word, s.id as sense_id, s.definition as definition,
                       s.definition_en as definition_en, s.example_en as example_en
                ORDER BY w.frequency_rank
            """
            result = session.run(query, word=target_word)
        else:
            query = """
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true
                  AND NOT EXISTS((s)-[:VERIFIED_BY]->(:Question))
                RETURN w.name as word, s.id as sense_id, s.definition as definition,
                       s.definition_en as definition_en, s.example_en as example_en
                ORDER BY w.frequency_rank
            """
            result = session.run(query)
        
        missing_questions = list(result)
        
        if not missing_questions:
            print("✅ No enriched senses missing verification questions!")
            return
        
        print(f"Found {len(missing_questions)} enriched sense(s) missing verification questions:")
        for record in missing_questions:
            print(f"  - {record['word']}: {record['sense_id']}")
        print()
        
        # Group by word
        words_to_fix = {}
        for record in missing_questions:
            word = record['word']
            if word not in words_to_fix:
                words_to_fix[word] = []
            words_to_fix[word].append({
                'sense_id': record['sense_id'],
                'definition': record['definition'],
                'definition_en': record['definition_en'],
                'example_en': record['example_en']
            })
        
        print(f"Processing {len(words_to_fix)} word(s)...")
        print()
        
        # For each word, get all its senses (including the ones missing questions)
        # and re-enrich to create questions
        for word, missing_senses in words_to_fix.items():
            print(f"Processing '{word}' ({len(missing_senses)} sense(s) missing questions)...")
            
            # Get all senses for this word to create proper skeletons
            all_senses_result = session.run("""
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                RETURN s.id as sense_id, s.definition as definition,
                       s.skeleton_phrases as skeleton_phrases
                ORDER BY s.id
            """, word=word)
            
            all_senses = list(all_senses_result)
            
            # Create skeletons in the format expected by get_enrichment
            skeletons = []
            for sense in all_senses:
                skeletons.append({
                    'id': sense['sense_id'],
                    'def': sense['definition'] or '',
                    'phrases': sense.get('skeleton_phrases', []) or []
                })
            
            if not skeletons:
                print(f"  ⚠️ No skeletons found for '{word}'. Skipping.")
                continue
            
            try:
                # Re-enrich to generate questions
                print(f"  Calling Gemini API to generate questions...")
                
                # Retry logic for API calls
                max_retries = 3
                enriched_data = None
                
                for attempt in range(max_retries):
                    try:
                        enriched_data = get_enrichment(word, skeletons, mock=False)
                        break
                    except Exception as api_error:
                        if attempt < max_retries - 1:
                            print(f"  ⚠️ API error (attempt {attempt + 1}/{max_retries}): {api_error}")
                            print(f"  Retrying...")
                            import time
                            time.sleep(2 * (attempt + 1))  # Exponential backoff
                        else:
                            raise
                
                if enriched_data:
                    # Filter to only the senses that were missing questions
                    # (in case enrichment returns more than we need)
                    missing_sense_ids = {s['sense_id'] for s in missing_senses}
                    filtered_data = [
                        d for d in enriched_data 
                        if d['sense_id'] in missing_sense_ids
                    ]
                    
                    if filtered_data:
                        # Only update the question creation part
                        # We don't want to overwrite existing enrichment data
                        with conn.get_session() as update_session:
                            # Create Question Nodes (Verified By) for missing questions
                            query_quiz = """
                            UNWIND $data AS row
                            MATCH (s:Sense {id: row.sense_id})
                            WHERE s.enriched = true
                              AND NOT EXISTS((s)-[:VERIFIED_BY]->(:Question))
                            MERGE (q:Question {id: row.sense_id + '_q'})
                            SET q.text = row.quiz.question,
                                q.options = row.quiz.options,
                                q.answer = row.quiz.answer,
                                q.explanation = row.quiz.explanation
                            MERGE (s)-[:VERIFIED_BY]->(q)
                            """
                            update_session.run(query_quiz, data=filtered_data)
                        
                        print(f"  ✅ Created {len(filtered_data)} verification question(s)")
                    else:
                        print(f"  ⚠️ No matching enriched data returned for missing senses")
                        print(f"  Expected sense IDs: {missing_sense_ids}")
                        if enriched_data:
                            returned_ids = [d['sense_id'] for d in enriched_data]
                            print(f"  Returned sense IDs: {returned_ids}")
                else:
                    print(f"  ⚠️ No enriched data returned from API")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print()
        print("=" * 80)
        print("VERIFICATION COMPLETE")
        print("=" * 80)
        
        # Verify fix
        verify_result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched = true
              AND NOT EXISTS((s)-[:VERIFIED_BY]->(:Question))
            RETURN count(s) as remaining
        """).single()
        
        remaining = verify_result['remaining']
        if remaining == 0:
            print("✅ All enriched senses now have verification questions!")
        else:
            print(f"⚠️ {remaining} enriched sense(s) still missing verification questions.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix enriched senses missing verification questions")
    parser.add_argument("--word", type=str, help="Specific word to fix (e.g., 'bank')")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            fix_missing_verification(conn, target_word=args.word)
        else:
            print("❌ Failed to connect to Neo4j database.")
            sys.exit(1)
    finally:
        conn.close()

