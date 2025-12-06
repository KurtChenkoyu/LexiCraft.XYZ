"""
LexiScan: Vocabulary Inventory Prototype
A CLI tool to verify user knowledge of specific word meanings.

Usage:
    python3 -m src.lexiscan --word run
    python3 -m src.lexiscan --word run --demo  # Non-interactive demo
"""

import argparse
import random
from src.database.neo4j_connection import Neo4jConnection

def run_lexiscan(conn: Neo4jConnection, target_word: str, demo: bool = False):
    print(f"🔍 LexiScan: Analyzing '{target_word}'...\n")
    
    with conn.get_session() as session:
        # 1. Fetch Senses and Questions
        result = session.run("""
            MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
            OPTIONAL MATCH (s)-[:VERIFIED_BY]->(q:Question)
            RETURN s.id, s.definition_en, s.definition_zh, q.text, q.options, q.answer, q.explanation
            ORDER BY s.id
        """, word=target_word)
        
        records = list(result)
        if not records:
            print(f"❌ Word '{target_word}' not found or has no senses.")
            return

        score = 0
        total = 0
        questions_found = 0
        
        for i, record in enumerate(records, 1):
            print(f"--- Meaning {i} ---")
            print(f"📖 Definition: {record['s.definition_en'] or 'N/A'}")
            print(f"📖 (Chinese): {record['s.definition_zh'] or 'N/A'}")
            
            # If no question exists (e.g., not enriched yet), skip
            if not record['q.text']:
                print(f"⚠️  (No assessment available for this meaning - not enriched yet)")
                print()
                continue
            
            questions_found += 1
            total += 1
            
            # Present MCQ
            print(f"\n❓ Question: {record['q.text']}")
            options = record['q.options'] or []
            for idx, opt in enumerate(options):
                marker = "✓" if idx == record['q.answer'] else " "
                print(f"   {marker} {chr(65+idx)}. {opt}")
            
            # Get Input (or simulate in demo mode)
            if demo:
                # In demo mode, randomly answer (or always get it right)
                user_idx = record['q.answer']  # Always correct in demo
                choice = chr(65 + user_idx)
                print(f"\n[DEMO MODE] Simulated Answer: {choice}")
            else:
                # Interactive mode
                while True:
                    choice = input("\nYour Answer (A/B/C/D): ").upper()
                    if choice in ['A', 'B', 'C', 'D']:
                        user_idx = ord(choice) - 65
                        break
                    print("Invalid choice. Please enter A, B, C, or D.")
            
            # Check Answer
            correct_idx = record['q.answer']
            if user_idx == correct_idx:
                print("✅ CORRECT!")
                score += 1
            else:
                print(f"❌ INCORRECT. The right answer was {chr(65+correct_idx)}.")
                if record['q.explanation']:
                    print(f"   💡 Explanation: {record['q.explanation']}")
            
            print()

        print("="*60)
        if total == 0:
            print(f"⚠️  No questions found for '{target_word}'.")
            print("   This word may not have been enriched yet.")
            print("   Run: python3 -m src.main_factory --limit 50")
        else:
            print(f"📊 Final Score for '{target_word}': {score}/{total}")
            if score == total:
                print("🌟 MASTERED: You know all meanings of this word!")
            elif score > 0:
                print("⚠️  PARTIAL: You missed some nuances.")
            else:
                print("📚 LEARN: This word is new to you.")
        print("="*60)

def list_available_words(conn: Neo4jConnection):
    """List words that have questions available."""
    print("📋 Words with Questions Available:\n")
    
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)-[:VERIFIED_BY]->(q:Question)
            WITH w, count(q) as question_count
            RETURN w.name as word, question_count, w.frequency_rank as rank
            ORDER BY rank ASC
            LIMIT 20
        """)
        
        words = list(result)
        if not words:
            print("❌ No words with questions found.")
            print("   Run: python3 -m src.main_factory --limit 50")
        else:
            for record in words:
                print(f"  • {record['word']} ({record['question_count']} questions)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LexiScan: Vocabulary Assessment Tool")
    parser.add_argument("--word", type=str, help="Target word to assess")
    parser.add_argument("--demo", action="store_true", help="Demo mode (non-interactive)")
    parser.add_argument("--list", action="store_true", help="List words with questions available")
    args = parser.parse_args()
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            if args.list:
                list_available_words(conn)
            elif args.word:
                run_lexiscan(conn, args.word, demo=args.demo)
            else:
                parser.print_help()
                print("\n💡 Tip: Use --list to see available words")
    finally:
        conn.close()
