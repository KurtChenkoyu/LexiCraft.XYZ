"""
Pedagogical Evaluation: LLM-based Assessment

Uses Gemini to evaluate the pedagogical effectiveness of Stage 2 examples:
- Do examples actually help learners understand the sense?
- Are contrastive examples clear enough?
- Do synonym examples show meaningful differences?
- Do confusion examples actually clarify distinctions?
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from src.database.neo4j_connection import Neo4jConnection

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)


PEDAGOGICAL_EVALUATION_PROMPT = """
You are an expert EFL curriculum evaluator specializing in vocabulary instruction for Taiwan B1/B2 learners.

Evaluate the pedagogical effectiveness of these example sentences for a specific word sense.

TARGET SENSE:
Word: "{word}"
Sense ID: {sense_id}
Definition (EN): {definition_en}
Definition (ZH): {definition_zh}

EXAMPLES BY LAYER:

Layer 1 - Contextual Support:
{contextual_examples}

Layer 2 - Opposite Examples (if any):
{opposite_examples}

Layer 3 - Similar Examples (if any):
{similar_examples}

Layer 4 - Confused Examples (if any):
{confused_examples}

EVALUATION CRITERIA:

1. CONTEXTUAL SUPPORT (Layer 1) - 30% weight
   - Do examples clearly illustrate the target sense?
   - Are examples varied enough to show different contexts?
   - Would a B1/B2 learner understand the sense from these examples?

2. CONTRASTIVE CLARITY (Layer 2) - 20% weight
   - Do opposite examples show clear contrast?
   - Would learners understand what the word is NOT?
   - Is the distinction clear and helpful?

3. NUANCE DIFFERENTIATION (Layer 3) - 20% weight
   - Do similar examples show meaningful differences?
   - Would learners understand when to use this word vs. synonyms?
   - Are the differences clear and practical?

4. CONFUSION CLARIFICATION (Layer 4) - 20% weight
   - Do confused examples actually clarify the distinction?
   - Would learners avoid common errors after seeing these?
   - Is the difference between confused words clear?

5. OVERALL EFFECTIVENESS - 10% weight
   - Would these examples help a Taiwan EFL learner understand and use this word correctly?
   - Are examples appropriate for B1/B2 level?

OUTPUT FORMAT (JSON):
{{
    "overall_score": 0.0-1.0,
    "contextual_score": 0.0-1.0,
    "contrast_score": 0.0-1.0,
    "nuance_score": 0.0-1.0,
    "clarification_score": 0.0-1.0,
    "effectiveness_score": 0.0-1.0,
    "strengths": ["List 2-3 strengths"],
    "weaknesses": ["List 2-3 areas for improvement"],
    "recommendation": "PASS" | "NEEDS_REVIEW" | "FAIL",
    "summary": "2-3 sentence overall assessment"
}}

EVALUATION STANDARDS:
- PASS: overall_score ≥ 0.75, all layer scores ≥ 0.7
- NEEDS_REVIEW: overall_score 0.6-0.74, or some layer scores < 0.7
- FAIL: overall_score < 0.6, or critical pedagogical issues

Be thorough but fair. Focus on whether examples would actually help learners.
"""


def format_examples_for_prompt(examples: list, layer_name: str) -> str:
    """Format examples for the evaluation prompt."""
    if not examples:
        return f"None provided for {layer_name}."
    
    formatted = []
    for i, ex in enumerate(examples, 1):
        en = ex.get("example_en", "")
        zh = ex.get("example_zh", "")
        rel_word = ex.get("relationship_word", "")
        
        if rel_word:
            formatted.append(f"{i}. EN: {en}\n   ZH: {zh}\n   Related word: {rel_word}")
        else:
            formatted.append(f"{i}. EN: {en}\n   ZH: {zh}")
    
    return "\n".join(formatted)


def evaluate_sense_pedagogy(
    word: str,
    sense_id: str,
    definition_en: str,
    definition_zh: str,
    contextual: list,
    opposite: list,
    similar: list,
    confused: list
) -> Optional[Dict[str, Any]]:
    """Evaluate pedagogical effectiveness using Gemini."""
    if not API_KEY:
        print("⚠️ GOOGLE_API_KEY not found. Skipping LLM evaluation.")
        return None
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = PEDAGOGICAL_EVALUATION_PROMPT.format(
        word=word,
        sense_id=sense_id,
        definition_en=definition_en,
        definition_zh=definition_zh,
        contextual_examples=format_examples_for_prompt(contextual, "Contextual Support"),
        opposite_examples=format_examples_for_prompt(opposite, "Opposite Examples"),
        similar_examples=format_examples_for_prompt(similar, "Similar Examples"),
        confused_examples=format_examples_for_prompt(confused, "Confused Examples")
    )
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1  # Low temperature for consistency
            }
        )
        
        response_text = response.text.strip()
        
        # Fix common JSON issues
        import re
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
        
        try:
            evaluation = json.loads(response_text)
            return evaluation
        except json.JSONDecodeError as e:
            # Try to extract from markdown
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                evaluation = json.loads(json_text)
                return evaluation
            else:
                print(f"JSON Parse Error: {e}")
                return None
                
    except Exception as e:
        print(f"LLM Evaluation Error: {e}")
        return None


def evaluate_example_pedagogy(conn: Neo4jConnection, limit: int = 10):
    """Evaluate pedagogical effectiveness of Stage 2 examples."""
    print("=" * 60)
    print("STAGE 2: PEDAGOGICAL EFFECTIVENESS EVALUATION")
    print("=" * 60)
    
    if not API_KEY:
        print("⚠️ GOOGLE_API_KEY not found. Cannot run LLM evaluation.")
        return
    
    with conn.get_session() as session:
        # Get Stage 2 enriched senses
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.stage2_enriched = true
            RETURN w.name as word, s.id as sense_id,
                   s.definition_en as definition_en,
                   s.definition_zh as definition_zh,
                   s.examples_contextual as contextual,
                   s.examples_opposite as opposite,
                   s.examples_similar as similar,
                   s.examples_confused as confused
            LIMIT $limit
        """, limit=limit)
        
        records = list(result)
        if not records:
            print("❌ No Stage 2 enriched senses found.")
            return
        
        print(f"Evaluating {len(records)} senses...\n")
        
        evaluations = []
        stats = {
            "pass": 0,
            "needs_review": 0,
            "fail": 0,
            "total": 0,
            "avg_overall_score": 0.0
        }
        
        for record in records:
            word = record["word"]
            sense_id = record["sense_id"]
            definition_en = record.get("definition_en", "")
            definition_zh = record.get("definition_zh", "")
            # Parse JSON strings if they exist
            contextual_raw = record.get("contextual") or "[]"
            opposite_raw = record.get("opposite") or "[]"
            similar_raw = record.get("similar") or "[]"
            confused_raw = record.get("confused") or "[]"
            
            contextual = json.loads(contextual_raw) if isinstance(contextual_raw, str) else (contextual_raw or [])
            opposite = json.loads(opposite_raw) if isinstance(opposite_raw, str) else (opposite_raw or [])
            similar = json.loads(similar_raw) if isinstance(similar_raw, str) else (similar_raw or [])
            confused = json.loads(confused_raw) if isinstance(confused_raw, str) else (confused_raw or [])
            
            print(f"Evaluating {word} ({sense_id})...")
            
            evaluation = evaluate_sense_pedagogy(
                word, sense_id, definition_en, definition_zh,
                contextual, opposite, similar, confused
            )
            
            if evaluation:
                evaluations.append({
                    "word": word,
                    "sense_id": sense_id,
                    "evaluation": evaluation
                })
                
                stats["total"] += 1
                stats["avg_overall_score"] += evaluation.get("overall_score", 0.0)
                
                recommendation = evaluation.get("recommendation", "NEEDS_REVIEW")
                if recommendation == "PASS":
                    stats["pass"] += 1
                elif recommendation == "FAIL":
                    stats["fail"] += 1
                else:
                    stats["needs_review"] += 1
        
        # Report results
        if stats["total"] > 0:
            stats["avg_overall_score"] /= stats["total"]
        
        print(f"\n📊 Evaluation Statistics:")
        print(f"  Total evaluated: {stats['total']}")
        print(f"  ✅ PASS: {stats['pass']} ({stats['pass']/max(stats['total'],1)*100:.1f}%)")
        print(f"  ⚠️  NEEDS_REVIEW: {stats['needs_review']} ({stats['needs_review']/max(stats['total'],1)*100:.1f}%)")
        print(f"  ❌ FAIL: {stats['fail']} ({stats['fail']/max(stats['total'],1)*100:.1f}%)")
        print(f"  Average overall score: {stats['avg_overall_score']:.2f}")
        
        # Show detailed results
        if evaluations:
            print("\n📋 Detailed Results:")
            for eval_data in evaluations[:5]:  # Show first 5
                word = eval_data["word"]
                sense_id = eval_data["sense_id"]
                eval_result = eval_data["evaluation"]
                
                print(f"\n{word} ({sense_id}):")
                print(f"  Overall Score: {eval_result.get('overall_score', 0):.2f}")
                print(f"  Recommendation: {eval_result.get('recommendation', 'N/A')}")
                print(f"  Summary: {eval_result.get('summary', 'N/A')}")
                
                if eval_result.get("weaknesses"):
                    print(f"  Weaknesses: {', '.join(eval_result['weaknesses'][:2])}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="Number of senses to evaluate")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            evaluate_example_pedagogy(conn, limit=args.limit)
    finally:
        conn.close()

