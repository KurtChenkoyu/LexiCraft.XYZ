"""
Pipeline Step 2: Content Generation Level 1 (The Gemini Agent)
Enriches WordNet Senses with modern definitions, Chinese translations, examples, 
AND generates the "Validation Engine" (Questions & Phrases).

Usage:
    python3 -m src.agent --word bank  # Enrich specific word
    python3 -m src.agent --limit 10   # Enrich 10 pending words
    python3 -m src.agent --mock       # Simulate Level 1 content generation
"""

import os
import json
import argparse
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from src.database.neo4j_connection import Neo4jConnection
from src.models.learning_point import EnrichedSense, EnrichmentBatch

# Load environment variables from .env file
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("⚠️ WARNING: GOOGLE_API_KEY not found. Agent will fail if run without --mock.")

def get_mock_enrichment(word: str, skeletons: list) -> List[dict]:
    """
    Returns hardcoded data for testing without API key.
    """
    print(f"⚠️ Using MOCK data for '{word}'...")
    
    enriched_senses = []
    for i, skel in enumerate(skeletons):
        enriched_senses.append({
            "sense_id": skel['id'],
            "definition_en": f"Mock definition for {word} (Sense {i+1})",
            "definition_zh_translation": f"{word} 的測試定義 (字面翻譯 {i+1})",
            "definition_zh_explanation": f"{word} 的測試定義說明 (意思 {i+1})",
            "example_en": f"This is a mock example for {word}.",
            "example_zh_translation": f"這是 {word} 的測試例句 (字面翻譯)。",
            "example_zh_explanation": f"這是 {word} 的測試例句說明。",
            "quiz": {
                "question": f"What is the meaning of {word} in this context?",
                "options": [
                    "Wrong Answer 1",
                    f"Correct Answer for Sense {i+1}",
                    "Wrong Answer 2",
                    "Wrong Answer 3"
                ],
                "answer": 1,
                "explanation": "This is the correct answer because it matches the definition."
            },
            "mapped_phrases": [f"{word} phrase 1", f"{word} phrase 2"]
        })
        
    return enriched_senses

def get_enrichment(word: str, skeletons: list, mock: bool = False) -> List[dict]:
    """
    Calls Gemini to enrich a list of sense skeletons.
    """
    if mock:
        return get_mock_enrichment(word, skeletons)

    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing.")

    model = genai.GenerativeModel('gemini-2.0-flash')

    # Construct Prompt (IMPROVED for Data Quality)
    prompt = f"""
You are a helpful language learning guide helping Taiwan EFL learners understand English expressions. 
Your role is to help learners CONNECT with the language naturally, not to teach or correct them.
Focus on creating pathways that help learners see how English expressions work.

IMPORTANT: Vary your explanation style. Do NOT default to "想像一下" (imagine) for every explanation.
Use diverse approaches: direct descriptions, natural metaphors, examples, or comparisons.
Only use "想像一下" when it genuinely helps create a clear connection pathway.

Target Word: "{word}"

CRITICAL INSTRUCTIONS FOR DATA QUALITY:
1. PRIMARY SENSE PRIORITY: 
   - If a sense_id starts with "{word.lower()}" (e.g., "{word.lower()}.n.01"), this is the PRIMARY sense for this word.
   - PRIMARY senses should be enriched FIRST and with the MOST COMMON meaning.
   - If a sense_id does NOT start with "{word.lower()}" (e.g., "weather.v.01"), it is a SHARED sense from another word.
   - SHARED senses should only be included if they are genuinely relevant to "{word}" in common usage.
   - DO NOT use shared senses as the primary definition (e.g., don't define "brave" as "to cope with" from weather.v.01).

2. DEFINITION ACCURACY:
   - Each definition MUST accurately reflect the sense_id provided.
   - If the sense_id is "{word.lower()}.n.01", the definition should be the PRIMARY noun meaning of "{word}".
   - If the sense_id is "{word.lower()}.v.01", the definition should be the PRIMARY verb meaning of "{word}".
   - Cross-reference the WordNet definition in the skeleton to ensure accuracy.

3. CONTEXT & USAGE:
   - For PRIMARY senses: Provide clear, common usage examples.
   - For SECONDARY/SLANG senses (e.g., "bread" = money): 
     * Clearly indicate it's informal/slang in the definition.
     * Provide context in the example (e.g., "He makes a lot of bread" = money).
   - Include register markers when appropriate (formal/informal/slang).

4. POLYSEMY HANDLING:
   - If "{word}" has multiple valid meanings (e.g., "bread" = food AND money slang):
     * Enrich BOTH if they are common enough for B1/B2 learners.
     * Clearly distinguish them with context in examples.
     * Mark the primary meaning (most common) clearly.

Below are the raw WordNet meanings (skeletons) for "{word}":
{json.dumps(skeletons, indent=2)}

YOUR TASK:
1. IDENTIFY PRIMARY SENSES: 
   - Find all senses where sense_id starts with "{word.lower()}"
   - These are the PRIMARY meanings you MUST enrich.
   - Prioritize these over shared senses.

2. FILTER & ENRICH:
   - Keep only relevant senses for B1/B2 learners (max 3-5 most common).
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
         * IMPORTANT: If the word in this sense has a non-literal meaning (e.g., "break" meaning opportunity, not "to break something"), 
           you MUST show the connection pathway from literal to non-literal. This applies to abstract/metaphorical meanings.
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
     * Distractors should include other meanings of "{word}" (if polysemous).
     * Make it clear which sense is being tested.
   - Mapped Phrases: Map skeleton phrases to the correct sense, or suggest common collocations.

4. QUALITY CHECK:
   - Verify the definition matches the sense_id (not a shared sense from another word).
   - Ensure examples are natural and modern (not outdated).
   - Confirm literal translations show English structure clearly.
   - Confirm explanations actively identify and explain nuances, cultural context, and implied meanings that learners might miss.

Return a strict JSON object matching this schema:
{{
    "senses": [
        {{
            "sense_id": "...",
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
        }}
    ]
}}

IMPORTANT: Only return senses that are genuinely relevant to "{word}" and appropriate for B1/B2 learners. 
Prioritize PRIMARY senses (sense_id starts with "{word.lower()}") over shared senses.
"""

    try:
        # Generate Content (Force JSON mode if supported, or parse text)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse Response with better error handling
        response_text = response.text.strip()
        
        # Try to fix common JSON issues (trailing commas, etc.)
        # Remove trailing commas before closing brackets/braces
        import re
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            # If JSON parsing fails, try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                data = json.loads(json_text)
            else:
                raise json_err
        
        return data.get("senses", [])
    except Exception as e:
        print(f"Gemini API Error: {e}")
        if hasattr(e, 'pos'):
            print(f"  Error at position: {e.pos}")
            if hasattr(e, 'doc'):
                print(f"  Context: ...{e.doc[max(0, e.pos-50):e.pos+50]}...")
        return []

def update_graph(conn: Neo4jConnection, enriched_senses: list):
    """
    Updates Sense nodes AND creates Question/Phrase nodes in Neo4j.
    """
    with conn.get_session() as session:
        # 1. Update Sense Node
        query_sense = """
        UNWIND $data AS row
        MATCH (s:Sense {id: row.sense_id})
        SET s.definition_en = row.definition_en,
            s.definition_zh_translation = row.definition_zh_translation,
            s.definition_zh_explanation = row.definition_zh_explanation,
            s.example_en = row.example_en,
            s.example_zh_translation = row.example_zh_translation,
            s.example_zh_explanation = row.example_zh_explanation,
            s.enriched = true
        """
        session.run(query_sense, data=enriched_senses)

        # 2. Create Question Nodes (Verified By)
        query_quiz = """
        UNWIND $data AS row
        MATCH (s:Sense {id: row.sense_id})
        MERGE (q:Question {id: row.sense_id + '_q'})
        SET q.text = row.quiz.question,
            q.options = row.quiz.options,
            q.answer = row.quiz.answer,
            q.explanation = row.quiz.explanation
        MERGE (s)-[:VERIFIED_BY]->(q)
        """
        session.run(query_quiz, data=enriched_senses)

        # 3. Create Phrase Nodes (Maps To Sense)
        # We need to find the anchor word to link (:Phrase)-[:ANCHORED_TO]->(:Word)
        # We can infer it from the Sense connection
        query_phrases = """
        UNWIND $data AS row
        MATCH (s:Sense {id: row.sense_id})<-[:HAS_SENSE]-(w:Word)
        WITH s, w, row
        UNWIND row.mapped_phrases AS phrase_text
        MERGE (p:Phrase {text: phrase_text})
        MERGE (p)-[:MAPS_TO_SENSE]->(s)
        MERGE (p)-[:ANCHORED_TO]->(w)
        """
        session.run(query_phrases, data=enriched_senses)

def run_agent(conn: Neo4jConnection, target_word: str = None, limit: int = 10, mock: bool = False):
    print("🤖 Starting Gemini Agent (Validation Engine Upgrade)...")
    
    with conn.get_session() as session:
        # 1. Fetch Candidates (Words with unenriched senses)
        if target_word:
            result = session.run("""
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched IS NULL
                RETURN w.name as word, collect({id: s.id, def: s.definition}) as skeletons
            """, word=target_word)
        else:
            result = session.run("""
                MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched IS NULL
                WITH w, collect({id: s.id, def: s.definition}) as skeletons
                RETURN w.name as word, skeletons
                LIMIT $limit
            """, limit=limit)
            
        tasks = list(result)
        print(f"Found {len(tasks)} words to enrich.")
        
        for record in tasks:
            word = record["word"]
            skeletons = record["skeletons"]
            print(f"Enriching '{word}' ({len(skeletons)} senses)...")
            
            try:
                enriched_data = get_enrichment(word, skeletons, mock=mock)
                if enriched_data:
                    update_graph(conn, enriched_data)
                    print(f"  ✅ Enriched {len(enriched_data)} senses (with Quiz & Phrases).")
                else:
                    print(f"  ⚠️ No data returned for '{word}'.")
            except Exception as e:
                print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--word", type=str, help="Target word to enrich")
    parser.add_argument("--limit", type=int, default=10, help="Batch size")
    parser.add_argument("--mock", action="store_true", help="Use mock data (no API key)")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            run_agent(conn, target_word=args.word, limit=args.limit, mock=args.mock)
    finally:
        conn.close()
