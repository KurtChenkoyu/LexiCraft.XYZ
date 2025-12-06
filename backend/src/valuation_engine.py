"""
Valuation Engine: The Vocabulary Inventory Logic
Implements the Binary Search algorithm to estimate user vocabulary size.

Separates "Rank Logic" (In-Memory) from "Content Fetching" (Neo4j).
"""

import pandas as pd
from pathlib import Path
import random
import time
from src.database.neo4j_connection import Neo4jConnection

VOCAB_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "master_vocab.csv"

class RankMap:
    """
    Lightweight In-Memory Index of Rank -> Word.
    Allows instant lookups: 'What is the word at Rank 4000?'
    """
    def __init__(self):
        self.rank_to_word = {}
        self.max_rank = 0
        self._load_data()

    def _load_data(self):
        if not VOCAB_PATH.exists():
            raise FileNotFoundError(f"Master Vocab file not found at {VOCAB_PATH}")
        
        print(f"📊 Loading Rank Map from {VOCAB_PATH}...")
        df = pd.read_csv(VOCAB_PATH)
        
        # We use 'unified_rank' as the sorting key, but we need integer indices for Binary Search.
        # Strategy: Sort by unified_rank, then assign a sequential index (1...N).
        df = df.sort_values('unified_rank')
        
        # Create mapping: Sequential Index -> Word Name
        # We map 1-based Index to Word Name
        # Use row.word instead of row['word'] for namedtuples
        self.rank_to_word = {i+1: row.word for i, row in enumerate(df.itertuples())}
        self.max_rank = len(self.rank_to_word)
        print(f"✅ Rank Map Loaded: 1 to {self.max_rank}")

    def get_word_at_rank(self, rank: int) -> str:
        """Returns the word at the specified sequential rank."""
        # Clamp rank to valid range
        rank = max(1, min(rank, self.max_rank))
        return self.rank_to_word.get(rank)

class ValuationEngine:
    """
    Executes the Binary Search Inventory Check.
    """
    def __init__(self):
        self.rank_map = RankMap()
        self.conn = Neo4jConnection()

    def get_question_for_word(self, word: str):
        """
        Fetches ONE question for the target word from Neo4j.
        Prioritizes the most frequent sense if multiple exist.
        """
        with self.conn.get_session() as session:
            # Get the first available question for this word
            result = session.run("""
                MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)-[:VERIFIED_BY]->(q:Question)
                RETURN s.definition_en, q.text, q.options, q.answer
                LIMIT 1
            """, word=word)
            
            return result.single()

    def run_inventory_check(self, simulation_mode=False):
        """
        The Binary Search Loop.
        Hops through the Rank Map to find the user's vocabulary ceiling.
        """
        print("\n🚀 Starting Inventory Check (Binary Search)...")
        print(f"Range: 1 - {self.rank_map.max_rank}\n")
        
        low = 1
        high = self.rank_map.max_rank
        history = []

        # Stop when range is narrow enough (e.g., within 50 words)
        while (high - low) > 50:
            mid = (low + high) // 2
            target_word = self.rank_map.get_word_at_rank(mid)
            
            print(f"📍 Testing Rank {mid}: '{target_word}'")
            
            # 1. Fetch Question (Content)
            record = self.get_question_for_word(target_word)
            
            is_correct = False
            
            if not record:
                # If no question exists, we assume UNKNOWN for simulation,
                # but in prod we'd want to pick a nearby word that HAS a question.
                # For now, fail-safe is "Unknown"
                print(f"   ⚠️  No question found for '{target_word}'. (Not enriched yet)")
                is_correct = False 
            else:
                # 2. Administer Test (Simulation or Real)
                if simulation_mode:
                    # Simulate: User knows words with Rank < 2000 (example skill level)
                    true_skill = 2000 
                    is_correct = (mid <= true_skill)
                    print(f"   [SIM] User Skill {true_skill} vs Rank {mid} -> {'CORRECT' if is_correct else 'WRONG'}")
                    time.sleep(0.5)
                else:
                    # Real User Input
                    print(f"\n❓ {record['q.text']}")
                    for idx, opt in enumerate(record['q.options']):
                        print(f"   {chr(65+idx)}. {opt}")
                    
                    ans = input("   Answer (A/B/C/D): ").upper()
                    correct_idx = record['q.answer']
                    is_correct = (ord(ans) - 65) == correct_idx
                    
                    if is_correct:
                        print("   ✅ Correct!")
                    else:
                        print(f"   ❌ Wrong. (Answer: {chr(65+correct_idx)})")

            # 3. Update Range
            history.append((mid, is_correct))
            if is_correct:
                low = mid  # They know this, try higher
                print(f"   📈 Moving Up! New Range: {low}-{high}")
            else:
                high = mid # They failed, try lower
                print(f"   📉 Moving Down! New Range: {low}-{high}")
            
            print("-" * 40)

        estimated_vocab = low
        print(f"\n🏁 Inventory Complete.")
        print(f"Estimated Vocabulary Size: ~{estimated_vocab} words")
        return estimated_vocab

if __name__ == "__main__":
    engine = ValuationEngine()
    # Default to simulation mode
    engine.run_inventory_check(simulation_mode=True)
