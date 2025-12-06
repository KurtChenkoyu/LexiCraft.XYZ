"""
Retry Level 2 content generation for senses that failed due to JSON parse errors.
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection
from src.agent_stage2 import (
    fetch_relationships,
    get_multilayer_examples,
    update_graph_stage2
)

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("⚠️ WARNING: GOOGLE_API_KEY not found.")
    sys.exit(1)

# Only retry the 2 that still failed after first retry
FAILED_SENSES = [
    "discovery.n.02",
    "neat.s.03"
]


def retry_failed_senses():
    """Retry Level 2 generation for failed senses."""
    conn = Neo4jConnection()
    
    print("=" * 80)
    print(f"RETRYING {len(FAILED_SENSES)} FAILED SENSES")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    
    with conn.get_session() as session:
        for sense_id in FAILED_SENSES:
            print(f"\n{'='*80}")
            print(f"Processing: {sense_id}")
            print(f"{'='*80}")
            
            # Fetch sense data
            result = session.run("""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense {id: $sense_id})
                OPTIONAL MATCH (s)<-[:MAPS_TO_SENSE]-(p:Phrase)
                RETURN w.name as word,
                       s.id as sense_id,
                       s.definition_en as definition_en,
                       s.definition_zh as definition_zh,
                       s.pos as part_of_speech,
                       s.example_en as existing_example_en,
                       s.example_zh as existing_example_zh,
                       s.usage_ratio as usage_ratio,
                       w.frequency_rank as frequency_rank,
                       w.moe_level as moe_level,
                       w.cefr as cefr,
                       w.is_moe_word as is_moe_word,
                       collect(DISTINCT p.text) as phrases
            """, sense_id=sense_id)
            
            record = result.single()
            if not record:
                print(f"❌ Sense {sense_id} not found in database")
                error_count += 1
                continue
            
            word = record["word"]
            definition_en = record.get("definition_en", "")
            definition_zh = record.get("definition_zh", "")
            part_of_speech = record.get("part_of_speech")
            existing_example_en = record.get("existing_example_en")
            existing_example_zh = record.get("existing_example_zh")
            usage_ratio = record.get("usage_ratio")
            frequency_rank = record.get("frequency_rank")
            moe_level = record.get("moe_level")
            cefr = record.get("cefr")
            is_moe_word = record.get("is_moe_word", False)
            phrases = record.get("phrases") or []
            
            print(f"Word: {word}")
            print(f"Definition (EN): {definition_en}")
            print(f"Definition (ZH): {definition_zh}")
            
            try:
                # Fetch relationships
                relationships = fetch_relationships(conn, word, sense_id=sense_id)
                print(f"Relationships found:")
                print(f"  - Opposite: {len(relationships.get('opposite', []))}")
                print(f"  - Similar: {len(relationships.get('similar', []))}")
                print(f"  - Confused: {len(relationships.get('confused', []))}")
                
                # Generate examples with retry logic
                max_retries = 5
                examples = None
                
                for attempt in range(max_retries):
                    try:
                        print(f"\n🔄 Attempt {attempt + 1}/{max_retries}...")
                        examples = get_multilayer_examples(
                            sense_id,
                            word,
                            definition_en,
                            definition_zh,
                            relationships,
                            part_of_speech=part_of_speech,
                            existing_example_en=existing_example_en,
                            existing_example_zh=existing_example_zh,
                            usage_ratio=usage_ratio,
                            frequency_rank=frequency_rank,
                            moe_level=moe_level,
                            cefr=cefr,
                            is_moe_word=is_moe_word,
                            phrases=phrases,
                            mock=False
                        )
                        print("✅ Successfully generated examples")
                        break
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON Parse Error (attempt {attempt + 1}): {e}")
                        if attempt < max_retries - 1:
                            import time
                            wait_time = (attempt + 1) * 2  # Exponential backoff
                            print(f"   Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print("❌ All retries failed - JSON parsing issue persists")
                            print("   This may be due to invalid Unicode escapes in Gemini response")
                            error_count += 1
                            continue
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        import traceback
                        traceback.print_exc()
                        if attempt < max_retries - 1:
                            import time
                            wait_time = (attempt + 1) * 2
                            print(f"   Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            error_count += 1
                            continue
                
                if examples:
                    # Update graph (sense_id is already in examples object)
                    update_graph_stage2(conn, examples)
                    print(f"✅ Successfully updated {sense_id}")
                    success_count += 1
                else:
                    print(f"❌ Failed to generate examples for {sense_id}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Error processing {sense_id}: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {error_count}")
    print(f"Total: {len(FAILED_SENSES)}")


if __name__ == "__main__":
    retry_failed_senses()

