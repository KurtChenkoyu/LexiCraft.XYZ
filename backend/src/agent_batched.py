"""
Batched Version of Content Enrichment Agent (V7.2)
Processes multiple words in a single API call for better throughput.

Concept: Simple word list → JSON array response → bulk save

Usage:
    python3 -m src.agent_batched --batch-size 10 --limit 100
"""

import os
import json
import argparse
import time
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict
from src.database.neo4j_connection import Neo4jConnection
from src.agent import update_graph

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def chunk_list(items: List, size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [items[i:i+size] for i in range(0, len(items), size)]

def get_pending_words(conn: Neo4jConnection, limit: int = None, min_rank: int = None, max_rank: int = None) -> List[str]:
    """
    Get all words that need enrichment.
    Returns simple list of word strings.
    
    Args:
        conn: Neo4j connection
        limit: Maximum number of words to return
        min_rank: Minimum frequency rank (inclusive)
        max_rank: Maximum frequency rank (inclusive)
    """
    with conn.get_session() as session:
        query = """
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched IS NULL
        """
        
        params = {}
        
        # Add rank filtering if specified
        if min_rank is not None:
            query += " AND w.frequency_rank >= $min_rank"
            params["min_rank"] = min_rank
        if max_rank is not None:
            query += " AND w.frequency_rank <= $max_rank"
            params["max_rank"] = max_rank
        
        query += """
            RETURN DISTINCT w.name as word, w.frequency_rank as rank
            ORDER BY rank ASC
        """
        
        if limit:
            query += " LIMIT $limit"
            params["limit"] = limit
        
        result = session.run(query, **params)
        return [record["word"] for record in result]

def get_word_skeletons(conn: Neo4jConnection, word_list: List[str]) -> Dict[str, List[dict]]:
    """
    Fetch sense skeletons for a list of words from the database.
    
    Returns:
        Dictionary mapping word -> list of sense skeletons with their IDs
    """
    with conn.get_session() as session:
        result = session.run("""
            UNWIND $words AS word_name
            MATCH (w:Word {name: word_name})-[:HAS_SENSE]->(s:Sense)
            WHERE s.enriched IS NULL
            RETURN word_name, collect({
                id: s.id,
                def: s.definition,
                phrases: s.skeleton_phrases
            }) as skeletons
        """, words=word_list)
        
        word_skeletons = {}
        for record in result:
            word_skeletons[record["word_name"]] = record["skeletons"]
        return word_skeletons

def process_batch(word_list: List[str], conn: Neo4jConnection = None, mock: bool = False) -> List[dict]:
    """
    Process a batch of words in a single API call.
    Fetches actual sense skeletons from database and matches API response to real sense IDs.
    
    Args:
        word_list: Simple list of word strings (e.g., ["bank", "account", "money"])
        conn: Neo4j connection (required for non-mock mode)
        mock: If True, return mock data
    
    Returns:
        JSON array where each object contains enrichment data for one word/sense with real sense_id
    """
    if mock:
        # Mock: return array of mock data
        result = []
        for word in word_list:
            # Simple mock: one sense per word
            result.append({
                "word": word,
                "sense_id": f"{word}_sense_1",
                "definition_en": f"Mock definition for {word}",
                "definition_zh": f"{word} 的測試定義",
                "example_en": f"This is a mock example for {word}.",
                "example_zh": f"這是 {word} 的測試例句。",
                "quiz": {
                    "question": f"What is the meaning of {word}?",
                    "options": ["Wrong 1", f"Correct: {word}", "Wrong 2", "Wrong 3"],
                    "answer": 1,
                    "explanation": "Mock explanation"
                },
                "mapped_phrases": [f"{word} phrase 1"]
            })
        return result

    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing.")
    
    if not conn:
        raise ValueError("Neo4j connection required for non-mock mode.")

    # Fetch actual sense skeletons from database
    word_skeletons = get_word_skeletons(conn, word_list)
    
    # Build prompt with actual skeletons
    skeletons_data = {}
    for word in word_list:
        if word in word_skeletons and word_skeletons[word]:
            skeletons_data[word] = word_skeletons[word]
    
    if not skeletons_data:
        return []

    model = genai.GenerativeModel('gemini-2.0-flash')

    # Build improved prompt adapted for multiple words
    words_list = ", ".join([f'"{w}"' for w in word_list])
    prompt = f"""
You are a helpful language learning guide helping Taiwan EFL learners understand English expressions. 
Your role is to help learners CONNECT with the language naturally, not to teach or correct them.
Focus on creating pathways that help learners see how English expressions work.

IMPORTANT: Vary your explanation style. Do NOT default to "想像一下" (imagine) for every explanation.
Use diverse approaches: direct descriptions, natural metaphors, examples, or comparisons.
Only use "想像一下" when it genuinely helps create a clear connection pathway.

Target Words: {words_list}

CRITICAL INSTRUCTIONS FOR DATA QUALITY:
1. PRIMARY SENSE PRIORITY: 
   - For each word, if a sense_id starts with the word name (e.g., "bank.n.01" for "bank"), this is the PRIMARY sense.
   - PRIMARY senses should be enriched FIRST and with the MOST COMMON meaning.
   - If a sense_id does NOT start with the word name (e.g., "weather.v.01" for "brave"), it is a SHARED sense from another word.
   - SHARED senses should only be included if they are genuinely relevant to the word in common usage.
   - DO NOT use shared senses as the primary definition (e.g., don't define "brave" as "to cope with" from weather.v.01).

2. DEFINITION ACCURACY:
   - Each definition MUST accurately reflect the sense_id provided.
   - Cross-reference the WordNet definition in the skeleton to ensure accuracy.
   - Match the sense_id to the correct word (e.g., "bank.n.01" belongs to "bank", not another word).

3. CONTEXT & USAGE:
   - For PRIMARY senses: Provide clear, common usage examples.
   - For SECONDARY/SLANG senses (e.g., "bread" = money): 
     * Clearly indicate it's informal/slang in the definition.
     * Provide context in the example (e.g., "He makes a lot of bread" = money).
   - Include register markers when appropriate (formal/informal/slang).

4. POLYSEMY HANDLING:
   - If a word has multiple valid meanings (e.g., "bread" = food AND money slang):
     * Enrich BOTH if they are common enough for B1/B2 learners.
     * Clearly distinguish them with context in examples.
     * Mark the primary meaning (most common) clearly.

Below are the raw WordNet meanings (skeletons) for each word:
{json.dumps(skeletons_data, indent=2)}

YOUR TASK:
For EACH word in the list above:
1. IDENTIFY PRIMARY SENSES: 
   - Find all senses where sense_id starts with the word name (lowercase)
   - These are the PRIMARY meanings you MUST enrich.
   - Prioritize these over shared senses.

2. FILTER & ENRICH:
   - Keep only relevant senses for B1/B2 learners (max 3-5 most common per word).
   - For each sense:
     * Rewrite definition simply (B1/B2 level English).
     * For the definition, provide TWO Chinese versions:
       - Literal translation (word-for-word, shows English structure)
       - Explanation that identifies what it really means, especially nuances that might be missed
     * Write a modern, natural example sentence in English.
     * For the example, provide TWO Chinese versions:
       - Literal translation (word-for-word, shows how English constructs meaning)
       - Explanation that identifies what the sentence REALLY means, especially:
         * Nuances that might be easily missed when going from English to Chinese
         * Cultural context or implied meanings
         * For idiomatic expressions OR words with non-literal meanings (e.g., "break" = opportunity, not just "to break something"): 
           Help learners CONNECT the literal meaning to the idiomatic/non-literal meaning
           - CRITICAL: ALWAYS start by showing the literal meaning of the WORD itself FIRST (e.g., "break" = 打破/中斷)
           - Then show how this literal meaning extends to the idiomatic/non-literal meaning
           - If the word has a non-literal meaning in this context (like "break" meaning opportunity), you MUST show the pathway
           - Create a natural CONNECTION and PATHWAY - show how the meaning flows from literal to idiomatic
           - Show the semantic pathway clearly: literal word meaning → metaphor/evolution → idiomatic meaning
           - Structure: Start with literal word meaning → show metaphor/extension → arrive at idiomatic meaning
           - EXAMPLE: For "break" = opportunity, show: "break" (打破/中斷) → breaks barriers/obstacles → opportunity
           - VARY your explanation style - do NOT default to "想像一下" for every explanation
           - Use diverse approaches:
             * Direct descriptions: "原本的意思是...，在這裡引申為..." (original meaning...extends to...)
             * Natural metaphors: "就像..." (like), "如同..." (as if) - embedded naturally in explanation
             * Examples: "例如..." (for example)
             * Comparisons: "可以想成..." (can think of it as)
             * Only use "想像一下" when it genuinely helps create a clear pathway
           - ALWAYS show literal meaning first, then show the connection pathway - don't jump straight to idiomatic
           - CRITICAL: NEVER start the explanation with disconnection statements like "不是指..." or "不是...而是" - these create disconnection
           - CRITICAL: NEVER use "字面上...但實際上" (literally...but actually) - this creates disconnection
           - NEVER create disconnection anywhere - idioms are EXTENSIONS, help learners see the connection pathway
           - CRITICAL: Do NOT add any disconnection statements (like "不是...而是", "不是指...而是指", "這裡的...不是指...而是指") at the START, MIDDLE, or END
           - Once you've shown the pathway, stop - do NOT add clarifying disconnection statements at the end
           - The explanation should ONLY show the connection pathway - no disconnection statements at all
           - Focus on helping learners CONNECT naturally, not teaching them - be a guide, not a teacher
           
           * EXAMPLE OF GOOD EXPLANATION (shows connection pathway):
             "原本你被困住，前面有一道牆擋著你 (literal break)。這道牆突然出現一個缺口 (metaphorical break)，讓你可以通過，繼續前進。所以「a break」就像是打破了阻礙你前進的困境，給你帶來一個新的開始和更好的機會 (idiomatic meaning)。"
             
             This shows: literal → metaphor → idiomatic (creates pathway, not disconnection)
           
           * EXAMPLE OF BAD EXPLANATION (creates disconnection - AVOID):
             "「break」在這裡不是指打破東西，而是指一個好機會。" ❌
             
             This creates disconnection ("不是...而是") instead of showing connection pathway
           
           * REQUIRED STRUCTURE FOR IDIOMATIC EXPRESSIONS:
             1. Start with literal meaning: "break" = 打破/中斷
             2. Show metaphor/extension: "就像打破阻礙..."
             3. Arrive at idiomatic: "所以引申為機會"
         * Subtle differences that literal translation would lose
     * If it's a secondary/slang meaning, add context (e.g., "非正式用語" for informal).

3. VALIDATION ENGINE:
   - Quiz: Create a challenging MCQ for THIS specific sense.
     * Distractors should include other meanings of the same word (if polysemous).
     * Make it clear which sense is being tested.
   - Mapped Phrases: Map skeleton phrases to the correct sense, or suggest common collocations.

4. QUALITY CHECK:
   - Verify the definition matches the sense_id (not a shared sense from another word).
   - Ensure examples are natural and modern (not outdated).
   - Confirm literal translations show English structure clearly.
   - Confirm explanations actively identify and explain nuances, cultural context, and implied meanings that learners might miss.

Return a JSON Array where each object contains enrichment data for one word/sense combination:
[
    {{
        "word": "bank",
        "sense_id": "bank.n.01",
        "definition_en": "...",
        "definition_zh_translation": "...",
        "definition_zh_explanation": "...",
        "example_en": "...",
        "example_zh_translation": "...",
        "example_zh_explanation": "...",
        "quiz": {{
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "answer": 0,
            "explanation": "..."
        }},
        "mapped_phrases": ["phrase 1", "phrase 2"]
    }},
    ...
]

IMPORTANT: 
- Use the EXACT sense_id from the skeleton (the "id" field).
- Only return senses that are genuinely relevant to their word and appropriate for B1/B2 learners.
- Prioritize PRIMARY senses (sense_id starts with the word name) over shared senses.
- Include the "word" field in each object to identify which word the sense belongs to.
"""

    import time
    import random
    
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            data = json.loads(response.text)
            # Ensure it's a list (API might return object with array)
            if isinstance(data, dict) and "senses" in data:
                return data["senses"]
            elif isinstance(data, list):
                return data
            else:
                print(f"⚠️ Unexpected response format: {type(data)}")
                return []
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON Parse Error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** attempt + random.uniform(0, 1)
                print(f"   Retrying in {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"❌ Failed to parse JSON after {MAX_RETRIES} attempts")
                return []
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate limit" in error_str.lower():
                wait = 60 * (2 ** attempt) + random.uniform(0, 10)
                print(f"⚠️ Rate Limit (429) - Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
            elif "quota" in error_str.lower() or "403" in error_str:
                print(f"❌ Quota Exceeded: {e}")
                print("   Daily quota limit reached. Process will stop.")
                raise  # Re-raise to stop processing
            else:
                print(f"❌ Gemini API Error (batch): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    print(f"   Retrying in {wait:.1f}s...")
                    time.sleep(wait)
                else:
                    return []
    return []

def save_bulk_to_neo4j(conn: Neo4jConnection, enriched_data: List[dict]):
    """
    Bulk save enriched data to Neo4j.
    Takes a flat array of enriched senses (one per word/sense combination).
    
    This matches the conceptual code: save_bulk_to_neo4j(response)
    """
    if not enriched_data:
        return
    
    # Use existing update_graph which handles bulk updates
    # It expects list of enriched sense dicts, which matches our format
    update_graph(conn, enriched_data)

def run_batched_agent(conn: Neo4jConnection, batch_size: int = 10, limit: int = 100, mock: bool = False, min_rank: int = None, max_rank: int = None):
    """
    Runs the agent in batched mode (V7.2 style).
    
    Matches the conceptual code structure:
    1. Get pending words
    2. Chunk into batches
    3. Process each batch
    4. Bulk save
    
    Args:
        conn: Neo4j connection
        batch_size: Number of words to process per API call
        limit: Total number of words to process
        mock: Use mock data
        min_rank: Minimum frequency rank to process (inclusive)
        max_rank: Maximum frequency rank to process (inclusive)
    """
    rank_info = ""
    if min_rank is not None or max_rank is not None:
        rank_info = f" (ranks {min_rank or 'any'}-{max_rank or 'any'})"
    print(f"🤖 Starting Batched Gemini Agent V7.2 (batch_size={batch_size}{rank_info})...")
    
    # Step 1: Get all pending words (simple list)
    all_words = get_pending_words(conn, limit=limit, min_rank=min_rank, max_rank=max_rank)
    total_words = len(all_words)
    print(f"Found {total_words} words to enrich.")
    
    if total_words == 0:
        print("✅ No words need enrichment.")
        return
    
    # Step 2: Chunk into batches
    batches = chunk_list(all_words, size=batch_size)
    print(f"Processing {len(batches)} batches...")
    
    # Step 3: Process each batch
    total_processed = 0
    for i, word_list in enumerate(batches):
        batch_num = i + 1
        
        print(f"\n📦 Processing batch {batch_num}/{len(batches)}: {', '.join(word_list)}")
        
        try:
            # Process batch (fetch skeletons, call API, match to real IDs)
            enriched_array = process_batch(word_list, conn=conn, mock=mock)
            
            if enriched_array:
                # Step 4: Bulk save to Neo4j
                save_bulk_to_neo4j(conn, enriched_array)
                total_processed += len(enriched_array)
                print(f"  ✅ Batch {batch_num}: {len(enriched_array)} senses enriched")
            else:
                print(f"  ⚠️ Batch {batch_num}: No data returned")
            
            # Rate limit sleep (only if not mock)
            if not mock:
                time.sleep(2.0)  # Reduced sleep since we're batching
                
        except Exception as e:
            print(f"  ❌ Batch {batch_num} failed: {e}")
            # Continue with next batch
    
    print(f"\n✅ Batched enrichment complete. Processed {total_processed} senses across {total_words} words.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=5, help="Words per API call (default: 5)")
    parser.add_argument("--limit", type=int, default=100, help="Total words to process")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    parser.add_argument("--min-rank", type=int, default=None, help="Minimum frequency rank to process (inclusive)")
    parser.add_argument("--max-rank", type=int, default=None, help="Maximum frequency rank to process (inclusive)")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            run_batched_agent(
                conn, 
                batch_size=args.batch_size, 
                limit=args.limit, 
                mock=args.mock,
                min_rank=args.min_rank,
                max_rank=args.max_rank
            )
    finally:
        conn.close()

