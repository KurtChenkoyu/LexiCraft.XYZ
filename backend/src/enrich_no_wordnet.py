"""
Enrichment for words without WordNet data.
Uses Gemini to create learning content from scratch.

Handles:
- Pronouns (everyone, yourself, etc.)
- Conjunctions/prepositions (unless, nor, towards, etc.)
- Proper nouns (angeles, chris, etc.)
- Abbreviations (etc, dev, etc.)
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict
from src.database.neo4j_connection import Neo4jConnection

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def enrich_word_without_wordnet(word: str, word_type: str = None) -> dict:
    """
    Enrich a word that doesn't have WordNet data using Gemini.
    Creates a single sense with all learning content.
    
    Args:
        word: The word to enrich
        word_type: Optional hint (pronoun, conjunction, proper_noun, abbreviation)
    
    Returns:
        Dictionary with enrichment data (same format as normal enrichment)
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing.")
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Determine word type if not provided
    if not word_type:
        word_lower = word.lower()
        if word_lower in ['everyone', 'yourself', 'itself', 'themselves', 'himself', 'myself', 'ourselves', 'herself']:
            word_type = "pronoun"
        elif word_lower in ['unless', 'nor', 'towards', 'whose', 'whereas', 'whereby']:
            word_type = "conjunction_or_preposition"
        elif word_lower in ['angeles', 'chris', 'california', 'england'] or word[0].isupper():
            word_type = "proper_noun"
        elif word_lower in ['etc', 'dev', 'est', 'eur', 'ms', 'tv', 'com', 'cnet', 'fax']:
            word_type = "abbreviation"
        else:
            word_type = "unknown"
    
    prompt = f"""
    You are an expert EFL curriculum developer for Taiwan.
    
    Create learning content for the word: "{word}"
    Word Type: {word_type}
    
    This word does not have WordNet data, so create content from scratch.
    
    Create ONE sense with:
    1. Definition (B1/B2 level, simple English)
    2. Traditional Chinese translation (Taiwan usage)
    3. Modern example sentence + Traditional Chinese translation
    4. Quiz: HARDER-THAN-AVERAGE Multiple Choice Question
       - For pronouns: focus on grammar/usage
       - For conjunctions: focus on sentence structure
       - For proper nouns: focus on cultural/geographic context
       - For abbreviations: focus on expansion and usage
    5. Mapped Phrases: 1-2 common collocations or phrases
    
    Return a JSON object:
    {{
        "sense_id": "{word.lower()}.manual.01",
        "definition_en": "...",
        "definition_zh": "...",
        "example_en": "...",
        "example_zh": "...",
        "quiz": {{
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "answer": 0,
            "explanation": "..."
        }},
        "mapped_phrases": ["phrase 1", "phrase 2"]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        data = json.loads(response.text)
        
        # Ensure sense_id is set
        if "sense_id" not in data:
            data["sense_id"] = f"{word.lower()}.manual.01"
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON Parse Error for {word}: {e}")
        return None
    except Exception as e:
        print(f"❌ Gemini API Error for {word}: {e}")
        return None

def save_to_neo4j(conn: Neo4jConnection, word: str, enrichment_data: dict):
    """
    Save enrichment data to Neo4j.
    Creates Sense node if it doesn't exist, then enriches it.
    """
    if not enrichment_data:
        return False
    
    with conn.get_session() as session:
        # 1. Ensure Word exists
        session.run("""
            MERGE (w:Word {name: $word})
        """, word=word)
        
        # 2. Create or update Sense node
        sense_id = enrichment_data.get("sense_id", f"{word.lower()}.manual.01")
        
        session.run("""
            MATCH (w:Word {name: $word})
            MERGE (s:Sense {id: $sense_id})
            SET s.definition_en = $definition_en,
                s.definition_zh = $definition_zh,
                s.example_en = $example_en,
                s.example_zh = $example_zh,
                s.enriched = true,
                s.definition = $definition_en,
                s.pos = 'manual'
            MERGE (w)-[:HAS_SENSE]->(s)
        """, 
            word=word,
            sense_id=sense_id,
            definition_en=enrichment_data.get("definition_en", ""),
            definition_zh=enrichment_data.get("definition_zh", ""),
            example_en=enrichment_data.get("example_en", ""),
            example_zh=enrichment_data.get("example_zh", "")
        )
        
        # 3. Create Question node
        if "quiz" in enrichment_data:
            quiz = enrichment_data["quiz"]
            session.run("""
                MATCH (s:Sense {id: $sense_id})
                MERGE (q:Question {id: $question_id})
                SET q.text = $question,
                    q.options = $options,
                    q.answer = $answer,
                    q.explanation = $explanation
                MERGE (s)-[:VERIFIED_BY]->(q)
            """,
                sense_id=sense_id,
                question_id=f"{sense_id}_q",
                question=quiz.get("question", ""),
                options=quiz.get("options", []),
                answer=quiz.get("answer", 0),
                explanation=quiz.get("explanation", "")
            )
        
        # 4. Create Phrase nodes
        if "mapped_phrases" in enrichment_data:
            for phrase_text in enrichment_data.get("mapped_phrases", []):
                session.run("""
                    MATCH (s:Sense {id: $sense_id})<-[:HAS_SENSE]-(w:Word)
                    MERGE (p:Phrase {text: $phrase_text})
                    MERGE (p)-[:MAPS_TO_SENSE]->(s)
                    MERGE (p)-[:ANCHORED_TO]->(w)
                """,
                    sense_id=sense_id,
                    phrase_text=phrase_text
                )
        
        return True

def enrich_words_without_wordnet(conn: Neo4jConnection, word_list: List[str], min_rank: int = None, max_rank: int = None):
    """
    Enrich multiple words that don't have WordNet data.
    
    Args:
        conn: Neo4j connection
        word_list: List of words to enrich (if None, finds words in range)
        min_rank: Minimum frequency rank filter
        max_rank: Maximum frequency rank filter
    """
    if not word_list:
        # Find words without enriched senses in the specified range
        with conn.get_session() as session:
            query = """
                MATCH (w:Word)
                WHERE NOT EXISTS {
                    MATCH (w)-[:HAS_SENSE]->(s:Sense)
                    WHERE s.enriched = true
                }
            """
            params = {}
            
            if min_rank is not None:
                query += " AND w.frequency_rank >= $min_rank"
                params["min_rank"] = min_rank
            if max_rank is not None:
                query += " AND w.frequency_rank <= $max_rank"
                params["max_rank"] = max_rank
            
            query += " RETURN w.name as word ORDER BY w.frequency_rank ASC"
            
            result = session.run(query, **params)
            word_list = [record["word"] for record in result]
    
    if not word_list:
        print("✅ No words found to enrich.")
        return
    
    print(f"🤖 Enriching {len(word_list)} words without WordNet data...")
    print(f"Words: {', '.join(word_list[:10])}{'...' if len(word_list) > 10 else ''}")
    print()
    
    import time
    successful = 0
    failed = 0
    
    for i, word in enumerate(word_list, 1):
        print(f"📝 [{i}/{len(word_list)}] Enriching '{word}'...")
        
        try:
            enrichment_data = enrich_word_without_wordnet(word)
            
            if enrichment_data:
                if save_to_neo4j(conn, word, enrichment_data):
                    print(f"  ✅ Enriched '{word}'")
                    successful += 1
                else:
                    print(f"  ⚠️  Failed to save '{word}'")
                    failed += 1
            else:
                print(f"  ❌ No data returned for '{word}'")
                failed += 1
            
            # Rate limiting
            if i < len(word_list):
                time.sleep(2.0)
                
        except Exception as e:
            print(f"  ❌ Error enriching '{word}': {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"✅ Enrichment complete: {successful} successful, {failed} failed")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich words without WordNet data")
    parser.add_argument("--words", nargs="+", help="Specific words to enrich")
    parser.add_argument("--min-rank", type=int, help="Minimum frequency rank")
    parser.add_argument("--max-rank", type=int, help="Maximum frequency rank")
    parser.add_argument("--batch", type=str, choices=["1", "2", "3", "4"], help="Enrich unenriched words in specific batch")
    args = parser.parse_args()
    
    # Batch ranges
    batch_ranges = {
        "1": (1, 1000),
        "2": (1001, 2000),
        "3": (2001, 3000),
        "4": (3001, 3500),
    }
    
    conn = Neo4jConnection()
    try:
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            exit(1)
        
        if args.batch:
            min_rank, max_rank = batch_ranges[args.batch]
            print(f"🎯 Enriching unenriched words in Batch {args.batch} (ranks {min_rank}-{max_rank})")
            enrich_words_without_wordnet(conn, None, min_rank=min_rank, max_rank=max_rank)
        elif args.words:
            enrich_words_without_wordnet(conn, args.words)
        elif args.min_rank or args.max_rank:
            enrich_words_without_wordnet(conn, None, min_rank=args.min_rank, max_rank=args.max_rank)
        else:
            print("❌ Please specify --words, --batch, or --min-rank/--max-rank")
            parser.print_help()
    finally:
        conn.close()

